import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import re
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

# --- Deduplicate column names helper ---


def dedup_column_names(names):
    seen = {}
    result = []
    for name in names:
        if name not in seen:
            seen[name] = 1
            result.append(name)
        else:
            seen[name] += 1
            result.append(f"{name}.{seen[name]-1}")
    return result

# --- Block-aware column filtering helper ---


def get_column_blocks(date_row, header_row, target_date):
    col_blocks = []
    current_block = []

    for i in range(len(date_row)):
        date_val = str(date_row[i]).strip()
        header_val = str(header_row[i]).strip()

        if header_val.lower() == "time":
            if current_block:
                col_blocks.append(current_block)
            current_block = [i]
        elif current_block:
            current_block.append(i)

    if current_block:
        col_blocks.append(current_block)

    columns_to_keep = []
    for block in col_blocks:
        time_col = block[0]
        room_cols = block[1:]
        if any(target_date in str(date_row[i]) for i in room_cols):
            columns_to_keep.extend(block)

    return sorted(set(columns_to_keep))

# --- Normalize time slot formatting ---


def normalize_time_slot(text):
    return re.sub(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", r"\1 - \2", text.replace("-", " - "))

# --- Clean session names ---


def clean_session(session):
    try:
        if isinstance(session, str):
            session = session.split("[")[0]
            session = re.sub(r"\(.*?\)", "", session)
            session = re.sub(r"(Keynote\s*#\d+:)", r"\1<br>", session)
            return session.strip()
        elif pd.isna(session):
            return ''
        else:
            return str(session)
    except Exception:
        return str(session)

# --- Room-as-rows layout ---


def generate_schedule_plot(header_height, cell_height, font_size, date_str, input_path, output_pdf_path):
    df_raw = pd.read_csv(input_path, sep=',', header=None)
    date_row = df_raw.iloc[0]
    header_row = df_raw.iloc[1]

    columns_to_keep_idx = get_column_blocks(date_row, header_row, date_str)
    if not columns_to_keep_idx:
        print(f"⚠️ No data found for {date_str}")
        return

    df = df_raw.iloc[2:, columns_to_keep_idx]
    filtered_headers = df_raw.iloc[1, columns_to_keep_idx].astype(
        str).str.strip().tolist()
    df.columns = dedup_column_names(filtered_headers)

    time_cols = [col for col in df.columns if col.lower().startswith("time")]
    room_cols = [col for col in df.columns if col not in time_cols]
    if not time_cols:
        print(f"⚠️ No time column found for {date_str}")
        return
    time_col = time_cols[0]

    # Include only rows with [ASPLOS...] or [EuroSys...]
    df = df[df[room_cols].apply(
        lambda row: row.astype(str).str.contains(
            r"\[.*?(?:ASPLOS|EuroSys)", case=False).any(),
        axis=1
    )]

    # Normalize time slot text
    df[time_col] = df[time_col].astype(str).apply(normalize_time_slot)

    for col in room_cols:
        df[col] = df[col].apply(clean_session)

    def get_period(time_str):
        time_str = str(time_str)
        if "08" in time_str or "09" in time_str or "10" in time_str or "11" in time_str:
            return "Morning"
        elif "13" in time_str or "14" in time_str or "15" in time_str or "16" in time_str or "17" in time_str:
            return "Afternoon"
        else:
            return None

    df["Period"] = df[time_col].apply(get_period)
    df = df[df["Period"].notna()]

    reshaped = pd.DataFrame(index=room_cols, columns=["Morning", "Afternoon"])
    for period in ["Morning", "Afternoon"]:
        subset = df[df["Period"] == period]
        for room in room_cols:
            sessions = subset[room].dropna().unique()
            reshaped.loc[room, period] = "<br>".join(sessions)

    reshaped = reshaped.rename_axis("Room").reset_index()
    reshaped["Room"] = reshaped["Room"].apply(lambda x: f"<b>{x}</b>")

    base_colors = ['#C8D4E3', '#ffffff']
    if len(reshaped) % 2 == 0:
        base_colors.reverse()
    alt_colors = [base_colors[i % 2] for i in range(len(reshaped))]

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{col}</b>" for col in reshaped.columns],
            fill_color='#506784',
            font=dict(color='white', size=font_size),
            align=['left', 'center', 'center'],
            height=header_height
        ),
        cells=dict(
            values=[reshaped[col].tolist() for col in reshaped.columns],
            fill_color=[alt_colors],
            align=['left', 'center', 'center'],
            font=dict(size=font_size),
            height=cell_height
        )
    )])

    fig.update_layout(width=1280, height=720, margin=dict(l=0, r=0, t=0, b=0))
    pio.write_image(fig, output_pdf_path, format="pdf")
    print(f"PDF saved for {date_str}: {output_pdf_path}")

# --- Time-as-rows layout ---


def generate_schedule_plot2(header_height, cell_height, font_size, date_str, input_path, output_pdf_path):
    df_raw = pd.read_csv(input_path, sep=',', header=None)
    date_row = df_raw.iloc[0]
    header_row = df_raw.iloc[1]

    columns_to_keep_idx = get_column_blocks(date_row, header_row, date_str)
    if not columns_to_keep_idx:
        print(f"⚠️ No data found for {date_str}")
        return

    df = df_raw.iloc[2:, columns_to_keep_idx]
    filtered_headers = df_raw.iloc[1, columns_to_keep_idx].astype(
        str).str.strip().tolist()
    df.columns = dedup_column_names(filtered_headers)

    time_cols = [col for col in df.columns if col.lower().startswith("time")]
    room_cols = [col for col in df.columns if col not in time_cols]
    if not time_cols:
        print(f"⚠️ No time column found for {date_str}")
        return
    time_col = time_cols[0]

    # Include only rows with [ASPLOS...] or [EuroSys...]
    df = df[df[room_cols].apply(
        lambda row: row.astype(str).str.contains(
            r"\[.*?(?:ASPLOS|EuroSys)", case=False).any(),
        axis=1
    )]

    for col in room_cols:
        df[col] = df[col].apply(clean_session)

    df = df[[time_col] + room_cols]
    df = df.rename(columns={time_col: "Time"})
    df["Time"] = df["Time"].astype(str).apply(normalize_time_slot)
    df["Time"] = df["Time"].apply(lambda x: f"<b>{x}</b>")

    base_colors = ['#C8D4E3', '#ffffff']
    if len(df) % 2 == 0:
        base_colors.reverse()
    alt_colors = [base_colors[i % 2] for i in range(len(df))]

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{col}</b>" for col in df.columns],
            fill_color='#506784',
            font=dict(color='white', size=font_size),
            align=['left'] + ['center'] * (len(df.columns) - 1),
            height=header_height
        ),
        cells=dict(
            values=[df[col].tolist() for col in df.columns],
            fill_color=[alt_colors],
            align=['left'] + ['center'] * (len(df.columns) - 1),
            font=dict(size=font_size),
            height=cell_height
        )
    )])

    fig.update_layout(width=1280, height=720, margin=dict(l=0, r=0, t=0, b=0))
    pio.write_image(fig, output_pdf_path, format="pdf")
    print(f"PDF saved for {date_str}: {output_pdf_path}")


input = "input.ref.csv"

date = "2025-03-30"
generate_schedule_plot(
    header_height=72,
    cell_height=54,
    font_size=18,
    date_str=date,
    input_path=input,
    output_pdf_path=f"output/{date}-schedule.pdf"
)

date = "2025-03-31"
generate_schedule_plot(
    header_height=70,
    cell_height=50,
    font_size=18,
    date_str=date,
    input_path=input,
    output_pdf_path=f"output/{date}-schedule.pdf"
)

date = "2025-04-01"
generate_schedule_plot2(
    header_height=104,
    cell_height=77,
    font_size=18,
    date_str=date,
    input_path=input,
    output_pdf_path=f"output/{date}-schedule.pdf"
)

date = "2025-04-02"
generate_schedule_plot2(
    header_height=104,
    cell_height=154,
    font_size=18,
    date_str=date,
    input_path=input,
    output_pdf_path=f"output/{date}-schedule.pdf"
)

date = "2025-04-03"
generate_schedule_plot2(
    header_height=104,
    cell_height=154,
    font_size=18,
    date_str=date,
    input_path=input,
    output_pdf_path=f"output/{date}-schedule.pdf"
)
