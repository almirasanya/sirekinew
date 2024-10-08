import os
import json
import requests
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import schedule
import time
import threading

# Mengatur tema warna dan gaya
st.markdown(
    """
    <style>
    /* Mengatur warna sidebar */
    .css-1d391kg {
        background-color: #2F4F4F !important; /* Warna abu-abu tua */
    }
    
    /* Mengatur warna header */
    .css-1v0v2d3 { /* Ganti dengan class header yang benar jika berbeda */
        background-color: #003366 !important; /* Warna biru donker */
        color: white !important;
    }
    
    /* Mengatur warna teks dan link di sidebar */
    .css-1d391kg a {
        color: #4B9CDB !important;
        font-size: 16px !important;
    }

    .css-1d391kg a:hover {
        color: #003366 !important; /* Warna biru donker saat hover */
    }

    /* Mengatur tampilan utama */
    .css-1f2c1hf { /* Ganti dengan class tampilan utama yang benar jika berbeda */
        background-color: #D3D3D3 !important; /* Warna abu-abu terang untuk tampilan utama */
    }

    /* Mengatur ukuran dan posisi logo */
    .css-1a54z77 { /* Ganti dengan class logo yang benar jika berbeda */
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 100%;
        max-width: 150px; /* Batas maksimal ukuran logo */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Menambahkan logo BPS dan tulisan di sidebar
logo_path = "bps_logo.png"  # Pastikan path logo sesuai
st.sidebar.image(
    logo_path,
    width=80,
    use_column_width=False,
)  # Mengatur ukuran logo menjadi lebih kecil (80px)
st.sidebar.markdown(
    "<h2 style='text-align: center;'>SIREKI - BPS Kabupaten Pidie</h2>",
    unsafe_allow_html=True,
)

# Pilihan menu di sidebar
page = st.sidebar.selectbox(
    "Pilih Halaman", ["Input Survei", "Dashboard Progres", "Petugas"]
)


# Fungsi untuk mengatur akses Google Sheets
def configure_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    spreadsheet_id = (
        "1589Us7yAhYZH_AWTlKackgUkNtklbwYpPEeadscgXBM"  # Ganti dengan ID Spreadsheet
    )
    sheet = client.open_by_key(spreadsheet_id)
    return sheet


def get_sheet_names(sheet):
    return [worksheet.title for worksheet in sheet.worksheets()]


def get_worksheet(sheet, name):
    try:
        return sheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        return None


def create_new_sheet(sheet, name):
    return sheet.add_worksheet(title=name, rows="100", cols="20")


def add_sample_count_column(worksheet):
    try:
        headers = worksheet.row_values(1)
        if "Jumlah Sampel Selesai Data" not in headers:
            # Add the new column in the 7th position (column G)
            worksheet.add_cols(1)
            worksheet.update_cell(1, 7, "Jumlah Sampel Selesai Data")
    except Exception as e:
        st.error(f"Kesalahan dalam menambahkan kolom: {e}")


def handle_special_values(df):
    # Convert special float values to strings
    def convert(value):
        if isinstance(value, float):
            if value == float("inf") or value == float("-inf") or pd.isna(value):
                return str(value)
        elif isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d")  # Convert Timestamp to string
        return value

    return df.applymap(convert)


def add_reminder_status_column(worksheet):
    try:
        headers = worksheet.row_values(1)
        if "Reminder Status" not in headers:
            worksheet.add_cols(1)
            worksheet.update_cell(
                1, 8, "Reminder Status"
            )  # Kolom ke-8 untuk status reminder
    except Exception as e:
        print(f"Kesalahan dalam menambahkan kolom: {e}")


# Fungsi untuk mengirim pesan WhatsApp menggunakan Fonnte


def send_whatsapp_message_fonnte(
    phone_number, message, api_key, worksheet, row_index, reminder_type
):
    url = "https://api.fonnte.com/send"
    payload = {
        "target": phone_number,  # Nomor tujuan dalam format internasional
        "message": message,  # Isi pesan yang akan dikirim
    }
    headers = {
        "Authorization": api_key,  # Masukkan API Key Fonnte yang valid
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        print(f"Request URL: {url}")
        print(f"Request Payload: {payload}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")

        response.raise_for_status()

        if response.status_code == 200:
            response_data = response.json()
            # Update Google Sheet dengan status "Terkirim"
            worksheet.update_cell(row_index, 8, f"{reminder_type} - Terkirim")
            return response_data
        else:
            # Update Google Sheet dengan status "Gagal"
            worksheet.update_cell(row_index, 8, f"{reminder_type} - Gagal")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        worksheet.update_cell(row_index, 8, f"{reminder_type} - Gagal")
        return None


def send_whatsapp_message_fonnte(
    phone_number, message, api_key, worksheet, row_index, reminder_type
):
    url = "https://api.fonnte.com/send"
    payload = {
        "target": phone_number,  # Nomor tujuan dalam format internasional
        "message": message,  # Isi pesan yang akan dikirim
    }
    headers = {
        "Authorization": api_key,  # Masukkan API Key Fonnte yang valid
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        print(f"Request URL: {url}")
        print(f"Request Payload: {payload}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")

        response.raise_for_status()

        if response.status_code == 200:
            response_data = response.json()
            # Update Google Sheet dengan status "Terkirim"
            worksheet.update_cell(row_index, 8, f"{reminder_type} - Terkirim")
            return response_data
        else:
            # Update Google Sheet dengan status "Gagal"
            worksheet.update_cell(row_index, 8, f"{reminder_type} - Gagal")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        worksheet.update_cell(row_index, 8, f"{reminder_type} - Gagal")
        return None


# Fungsi untuk mengatur pengiriman pengingat
def schedule_reminders(row, api_key, worksheet, survey_name):
    try:
        start_date = datetime.strptime(row["Tanggal Mulai"], "%Y-%m-%d")
        end_date = datetime.strptime(row["Tanggal Selesai"], "%Y-%m-%d")

        today = datetime.today()  # Hari ini

        # Reminder 1: 2 hari setelah tanggal mulai
        reminder_1_date = start_date + timedelta(days=2)
        if today.date() == reminder_1_date.date():
            reminder_1_message = (
                f"_*Ini adalah pesan yang dibuat secara otomatis dari BPS Kabupaten Pidie*_\n\n"
                f"*Reminder Ke-1:* \n\n"
                f"Kepada {row['Nama Petugas']},\n\n"
                f"Ini adalah pengingat tentang tugas survei Anda pada:\n\n"
                f"Survei yang Diikuti: {survey_name}\n\n"  # Menggunakan nama sheet sebagai nama survei
                f"Tanggal Mulai: {row['Tanggal Mulai']}\n"
                f"Tanggal Selesai: {row['Tanggal Selesai']}\n"
                f"Jangan lupa mengisi progres pendataan hari ini!\n\n"
                f"Link input Progres: https://sirekipidie.streamlit.app/\n\n"
                f"Catatan!! Input Progres anda pada menu petugas dan jangan lupa save terlebih dahulu SIREKI-BPS\n\n"
                f"_Selamat Bertugas!!_"
            )
            send_whatsapp_message_fonnte(
                row["Nomor Telepon"],
                reminder_1_message,
                api_key,
                worksheet,
                row.name + 2,
                "Reminder 1",
            )

        # Reminder 2: 5 hari sebelum tanggal selesai
        reminder_2_date = end_date - timedelta(days=6)
        if today.date() == reminder_2_date.date():
            reminder_2_message = (
                f"_*Ini adalah pesan yang dibuat secara otomatis dari BPS Kabupaten Pidie*_\n\n"
                f"*Reminder Ke-2:* \n\n"
                f"Kepada {row['Nama Petugas']},\n\n"
                f"Ini adalah pengingat tentang tugas survei Anda pada:\n\n"
                f"Survei yang Diikuti: {survey_name}\n\n"  # Menggunakan nama sheet sebagai nama survei
                f"Tanggal Mulai: {row['Tanggal Mulai']}\n"
                f"Tanggal Selesai: {row['Tanggal Selesai']}\n"
                f"Jangan lupa mengisi progres pendataan hari ini!\n\n"
                f"Link input Progres: https://sirekipidie.streamlit.app/\n\n"
                f"Catatan!! Input Progres anda pada menu petugas dan jangan lupa save terlebih dahulu SIREKI-BPS\n\n"
                f"_Selamat Bertugas!!_"
            )
            send_whatsapp_message_fonnte(
                row["Nomor Telepon"],
                reminder_2_message,
                api_key,
                worksheet,
                row.name + 2,
                "Reminder 2",
            )

        # Reminder 3: 1 hari sebelum tanggal selesai
        reminder_3_date = end_date - timedelta(days=3)
        if today.date() == reminder_3_date.date():
            reminder_3_message = (
                f"_*Ini adalah pesan yang dibuat secara otomatis dari BPS Kabupaten Pidie*_\n\n"
                f"*Reminder Ke-3:* \n\n"
                f"Kepada {row['Nama Petugas']},\n\n"
                f"Ini adalah pengingat tentang tugas survei Anda pada:\n\n"
                f"Survei yang Diikuti: {survey_name}\n\n"  # Menggunakan nama sheet sebagai nama survei
                f"Tanggal Mulai: {row['Tanggal Mulai']}\n"
                f"Tanggal Selesai: {row['Tanggal Selesai']}\n"
                f"Jangan lupa mengisi progres pendataan hari ini!\n\n"
                f"Link input Progres: https://sirekipidie.streamlit.app/\n\n"
                f"Catatan!! Input Progres anda pada menu petugas dan jangan lupa save terlebih dahulu SIREKI-BPS\n\n"
                f"_Selamat Bertugas!!_"
            )
            send_whatsapp_message_fonnte(
                row["Nomor Telepon"],
                reminder_3_message,
                api_key,
                worksheet,
                row.name + 2,
                "Reminder 3",
            )

    except Exception as e:
        print(f"Kesalahan dalam penjadwalan reminder: {e}")


def process_reminders(df, api_key, worksheet, survey_name):
    for index, row in df.iterrows():
        schedule_reminders(row, api_key, worksheet, survey_name)


def run_reminders(sheet):
    api_key = "wsyuepP_Up4gtgdYYmT4"  # Ganti dengan API Key Fonnte yang valid

    for sheet_name in get_sheet_names(sheet):
        worksheet = get_worksheet(sheet, sheet_name)
        if worksheet:
            # Ambil data dari worksheet
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            # Proses reminder untuk data di worksheet ini
            process_reminders(df, api_key, worksheet, sheet_name)


# Fungsi untuk mengunggah data ke Google Sheets
def upload_to_google_sheets(df, worksheet):
    try:
        worksheet.clear()
        df = handle_special_values(df)
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        st.success("Data berhasil disimpan ke Google Sheets!")

        # Menjadwalkan pengiriman reminder setiap hari pukul 00:00
        schedule.every().day.at("16:05").do(run_reminders, sheet)

        # Menjalankan scheduler di thread terpisah
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Tunggu satu menit sebelum memeriksa lagi

        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()

    except Exception as e:
        st.error(f"Terjadi kesalahan saat menyimpan data: {e}")


# Menampilkan konten berdasarkan halaman yang dipilih
if page == "Input Survei":
    st.header("Upload Data Survei")

    # Menambahkan template Excel untuk diunduh
    st.markdown("#### Unduh Template Survei")
    with open("template_survei.xlsx", "rb") as file:
        st.download_button(
            label="Unduh Template Excel",
            data=file,
            file_name="template_survei.xlsx",
            mime="application/vnd.ms-excel",
        )
    st.text("Catatan!!")
    st.text("1. Untuk format Tanggal (YYYY-MM-DD)")
    st.text("2. Untun Nomor Telp di mulai dengan 628xxxxxxxx")

    # Input nama survei
    survey_name = st.text_input("Masukkan Nama Survei")
    if survey_name:
        sheet = configure_google_sheets()
        worksheet_names = get_sheet_names(sheet)

        if survey_name not in worksheet_names:
            st.warning(
                f"Sheet dengan nama '{survey_name}' tidak ditemukan. Membuat sheet baru."
            )
            worksheet = create_new_sheet(sheet, survey_name)
        else:
            worksheet = get_worksheet(sheet, survey_name)

        # Form untuk upload file
        uploaded_file = st.file_uploader("Unggah File Excel", type=["xlsx"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            upload_to_google_sheets(df, worksheet)
            add_sample_count_column(worksheet)

elif page == "Dashboard Progres":
    st.header("Dashboard Progres")

    # Input untuk memilih survei
    sheet = configure_google_sheets()
    worksheet_names = get_sheet_names(sheet)
    selected_survey = st.selectbox("Pilih Survei", worksheet_names)

    if selected_survey:
        worksheet = get_worksheet(sheet, selected_survey)
        if worksheet:
            # Ambil data petugas dan total sampel
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)

            # Tampilkan tabel progres pendataan
            if not df.empty:
                # Hitung total sampel per petugas
                st.subheader("Tabel Progres Pendataan Survei")
                df["Jumlah Sampel"] = pd.to_numeric(
                    df["Jumlah Sampel"], errors="coerce"
                ).fillna(0)
                df["Jumlah Sampel Selesai Data"] = pd.to_numeric(
                    df["Jumlah Sampel Selesai Data"], errors="coerce"
                ).fillna(0)
                df["Progres"] = (
                    df["Jumlah Sampel Selesai Data"] / df["Jumlah Sampel"] * 100
                )

                st.write(
                    df[
                        [
                            "Nama Petugas",
                            "Jumlah Sampel",
                            "Jumlah Sampel Selesai Data",
                            "Progres",
                        ]
                    ]
                )

                # Grafik bar untuk progres pendataan
                st.subheader("Grafik Progress Pendataan Survei")
                fig = go.Figure()

                fig.add_trace(
                    go.Bar(x=df["Nama Petugas"], y=df["Progres"], name="Progres (%)")
                )

                fig.update_layout(
                    title="Grafik Progress Pendataan Survei",
                    xaxis_title="Nama Petugas",
                    yaxis_title="Progres (%)",
                    yaxis=dict(range=[0, 100]),
                )

                st.plotly_chart(fig)

                # Hitung keseluruhan progres survei
                total_samples = df["Jumlah Sampel"].sum()
                total_samples_collected = df["Jumlah Sampel Selesai Data"].sum()

                if total_samples > 0:
                    overall_progress_percentage = (
                        total_samples_collected / total_samples
                    ) * 100
                else:
                    overall_progress_percentage = 0

                # Tampilkan progres keseluruhan
                st.subheader("Progres Keseluruhan Survei")
                st.write(f"Total Jumlah Sampel: {total_samples}")
                st.write(
                    f"Total Jumlah Sampel yang Telah Dikumpulkan: {total_samples_collected}"
                )
                st.write(
                    f"Persentase Progres Keseluruhan: {overall_progress_percentage:.2f}%"
                )


elif page == "Petugas":
    st.header("Menu Petugas")
    sheet = configure_google_sheets()
    worksheet_names = get_sheet_names(sheet)

    selected_survey = st.selectbox("Pilih Survei", worksheet_names)
    if selected_survey:
        worksheet = get_worksheet(sheet, selected_survey)
        if worksheet:
            petugas_names = worksheet.col_values(
                1  # Assuming 'Nama Petugas' is in the first column
            )
            if "Nama Petugas" in petugas_names:
                petugas_names.remove("Nama Petugas")

            selected_petugas = st.selectbox("Pilih Nama Petugas", petugas_names)

            if selected_petugas:
                data = worksheet.get_all_records()
                petugas_data = [
                    row for row in data if row["Nama Petugas"] == selected_petugas
                ]

                if petugas_data:
                    st.write(pd.DataFrame(petugas_data))
                    # Add column for sample count if not already present
                    add_sample_count_column(worksheet)
                    # Input field for sample count
                    sample_count = st.number_input(
                        "Masukkan Jumlah Sampel yang Sudah di Data", min_value=0
                    )
                    if st.button("Simpan Jumlah Sampel"):
                        # Find the row index for the selected petugas
                        for i, row in enumerate(worksheet.get_all_records()):
                            if row["Nama Petugas"] == selected_petugas:
                                row_index = (
                                    i + 2
                                )  # Adjusting for 1-based index and header row
                                worksheet.update_cell(
                                    row_index, 7, sample_count  # Column G is index 7
                                )
                        st.success("Jumlah sampel berhasil disimpan.")
