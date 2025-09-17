import streamlit as st
import pandas as pd
from gtts import gTTS
from pydub import AudioSegment
from pydub.utils import which
import os
from io import BytesIO


# Cấu hình ffmpeg cho pydub
# AudioSegment.converter = which("ffmpeg")
# AudioSegment.ffprobe = which("ffprobe")

st.title("📘 Chuyển Excel thành MP3 học từ vựng")

# Upload file Excel
uploaded_file = st.file_uploader("Tải lên file Excel (.xlsx)", type=["xlsx"])

# Chọn ngôn ngữ
lang_option = st.selectbox("Chọn ngôn ngữ nguồn", ["Anh - Việt", "Trung - Việt"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if st.button("🚀 Chuyển đổi sang MP3"):
        # Tạo folder tmp
        if not os.path.exists("tmp"):
            os.makedirs("tmp")

        audio_segments = []

        for i, row in df.iterrows():
            source_word = str(row['A'])   # cột A: English hoặc Chinese
            vietnamese_meaning = str(row['B'])
            vietnamese_example = str(row['C'])
            source_example = str(row['D'])

            # Ngôn ngữ phát âm
            if lang_option == "Anh - Việt":
                lang_src = "en"
                example_prefix = "Example: "
            else:
                lang_src = "zh-cn"
                example_prefix = "例子: "  # tiếng Trung cho "Ví dụ"

            # 1. Đọc từ gốc lần 1
            tts1 = gTTS(text=source_word, lang=lang_src)
            path1 = f"tmp/src1_{i}.mp3"
            tts1.save(path1)
            audio_segments.append(AudioSegment.from_mp3(path1))
            audio_segments.append(AudioSegment.silent(duration=500))

            # 2. Đọc từ gốc lần 2
            tts2 = gTTS(text=source_word, lang=lang_src)
            path2 = f"tmp/src2_{i}.mp3"
            tts2.save(path2)
            audio_segments.append(AudioSegment.from_mp3(path2))

            # 3. Nghĩa tiếng Việt
            tts_vi = gTTS(text=f"Nghĩa là {vietnamese_meaning}", lang="vi")
            path_vi = f"tmp/vi_{i}.mp3"
            tts_vi.save(path_vi)
            audio_segments.append(AudioSegment.from_mp3(path_vi))
            audio_segments.append(AudioSegment.silent(duration=500))

            # 4. Ví dụ tiếng Việt
            tts_vi_ex = gTTS(text=f"Ví dụ: {vietnamese_example}", lang="vi")
            path_viex = f"tmp/viex_{i}.mp3"
            tts_vi_ex.save(path_viex)
            audio_segments.append(AudioSegment.from_mp3(path_viex))
            audio_segments.append(AudioSegment.silent(duration=500))

            # 5. Ví dụ tiếng Anh hoặc Trung
            tts_src_ex = gTTS(text=example_prefix + source_example, lang=lang_src)
            path_ex = f"tmp/src_ex_{i}.mp3"
            tts_src_ex.save(path_ex)
            audio_segments.append(AudioSegment.from_mp3(path_ex))
            audio_segments.append(AudioSegment.silent(duration=1000))

        # Ghép lại
        final_audio = AudioSegment.empty()
        for seg in audio_segments:
            final_audio += seg

        # Xuất file mp3 ra bộ nhớ
        mp3_buffer = BytesIO()
        final_audio.export(mp3_buffer, format="mp3")
        mp3_buffer.seek(0)

        # Cho phép tải file
        st.success("✅ Đã tạo file MP3 thành công!")
        st.download_button(
            label="💾 Tải MP3 về máy",
            data=mp3_buffer,
            file_name="tuvung.mp3",
            mime="audio/mp3"
        )
