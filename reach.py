import streamlit as st
import pandas as pd
import edge_tts
import asyncio
from pydub import AudioSegment
from pydub.utils import which
import os
from io import BytesIO

# Cấu hình ffmpeg
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

st.title("📘 Chuyển Excel thành MP3 học từ vựng (Nam / Nữ)")

# Upload file
uploaded_file = st.file_uploader("📂 Tải lên file Excel (.xlsx)", type=["xlsx"])

# Chọn ngôn ngữ
lang_option = st.selectbox(
    "🌐 Chọn ngôn ngữ nguồn",
    ["Anh - Việt", "Trung - Việt", "Hàn - Việt"]
)

# Chọn giọng đọc
gender_option = st.selectbox(
    "🎤 Chọn giọng đọc",
    ["Nữ", "Nam"]
)

# Chọn tốc độ
speed_map = {
    "0.5x (rất chậm)": 0.5,
    "0.75x (chậm)": 0.75,
    "1.0x (chuẩn)": 1.0,
    "1.25x (nhanh nhẹ)": 1.25,
    "1.5x (nhanh)": 1.5,
    "2.0x (rất nhanh)": 2.0
}
speed_label = st.selectbox("⚡ Tốc độ đọc", list(speed_map.keys()), index=2)
speed_option = speed_map[speed_label]


# ----------------------------
# Mapping giọng đọc
# ----------------------------
def get_voice(lang_src, gender):
    if lang_src == "en":
        return "en-US-JennyNeural" if gender == "Nữ" else "en-US-GuyNeural"
    elif lang_src == "ko":
        return "ko-KR-SunHiNeural" if gender == "Nữ" else "ko-KR-InJoonNeural"
    elif lang_src == "zh-cn":
        return "zh-CN-XiaoxiaoNeural" if gender == "Nữ" else "zh-CN-YunxiNeural"
    elif lang_src == "vi":
        return "vi-VN-HoaiMyNeural" if gender == "Nữ" else "vi-VN-NamMinhNeural"


# ----------------------------
# Hàm tạo audio bằng edge-tts
# ----------------------------
async def text_to_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)


# ----------------------------
# Hàm đổi tốc độ
# ----------------------------
def change_speed(sound, speed=1.0):
    new_frame_rate = int(sound.frame_rate * speed)
    return sound._spawn(
        sound.raw_data,
        overrides={"frame_rate": new_frame_rate}
    ).set_frame_rate(sound.frame_rate)


# ============================
# XỬ LÝ CHÍNH
# ============================
if uploaded_file:

    df = pd.read_excel(uploaded_file)
    excel_filename = uploaded_file.name
    mp3_filename = os.path.splitext(excel_filename)[0] + ".mp3"

    if st.button("🚀 Chuyển đổi sang MP3"):

        if not os.path.exists("tmp"):
            os.makedirs("tmp")

        audio_segments = []

        for i, row in df.iterrows():

            source_word = str(row['A'])
            vietnamese_meaning = str(row['B'])
            vietnamese_example = str(row['C'])
            source_example = str(row['D'])

            # Xác định ngôn ngữ
            if lang_option == "Anh - Việt":
                lang_src = "en"
                example_prefix = "Example: "
            elif lang_option == "Trung - Việt":
                lang_src = "zh-cn"
                example_prefix = "例子: "
            else:
                lang_src = "ko"
                example_prefix = "예: "

            voice_src = get_voice(lang_src, gender_option)
            voice_vi = get_voice("vi", gender_option)

            # ---------- 1. Từ gốc lần 1 ----------
            path1 = f"tmp/src1_{i}.mp3"
            asyncio.run(text_to_speech(source_word, voice_src, path1))
            audio_segments.append(AudioSegment.from_mp3(path1))
            audio_segments.append(AudioSegment.silent(duration=500))

            # ---------- 2. Từ gốc lần 2 ----------
            path2 = f"tmp/src2_{i}.mp3"
            asyncio.run(text_to_speech(source_word, voice_src, path2))
            audio_segments.append(AudioSegment.from_mp3(path2))

            # ---------- 3. Nghĩa ----------
            path_vi = f"tmp/vi_{i}.mp3"
            asyncio.run(text_to_speech(f"Nghĩa là {vietnamese_meaning}", voice_vi, path_vi))
            audio_segments.append(AudioSegment.from_mp3(path_vi))
            audio_segments.append(AudioSegment.silent(duration=500))

            # ---------- 4. Ví dụ tiếng Việt ----------
            path_viex = f"tmp/viex_{i}.mp3"
            asyncio.run(text_to_speech(f"Ví dụ: {vietnamese_example}", voice_vi, path_viex))
            audio_segments.append(AudioSegment.from_mp3(path_viex))
            audio_segments.append(AudioSegment.silent(duration=500))

            # ---------- 5. Ví dụ tiếng nguồn ----------
            path_ex = f"tmp/src_ex_{i}.mp3"
            asyncio.run(text_to_speech(example_prefix + source_example, voice_src, path_ex))
            audio_segments.append(AudioSegment.from_mp3(path_ex))

            # Nghỉ 3 giây giữa các từ
            audio_segments.append(AudioSegment.silent(duration=3000))

        # Ghép file
        final_audio = AudioSegment.empty()
        for seg in audio_segments:
            final_audio += seg

        # Đổi tốc độ
        final_audio = change_speed(final_audio, speed_option)

        # Xuất ra bộ nhớ
        mp3_buffer = BytesIO()
        final_audio.export(mp3_buffer, format="mp3")
        mp3_buffer.seek(0)

        st.success(f"✅ Đã tạo file MP3 thành công ({speed_label} - {gender_option})!")
        st.audio(mp3_buffer, format="audio/mp3")

        st.download_button(
            label="💾 Tải MP3 về máy",
            data=mp3_buffer,
            file_name=mp3_filename,
            mime="audio/mp3"
        )
