package com.neoapps.neotube;

import com.arthenica.mobileffmpeg.Config;
import com.arthenica.mobileffmpeg.FFmpeg;

public class FFmpegKitBridge {
    public static String convertAudio(String inputPath, String outputPath, String format) {
        String codec = audioCodec(format);
        String[] command = new String[] {
            "-y",
            "-i", inputPath,
            "-vn",
            "-codec:a", codec,
            outputPath
        };

        int returnCode = FFmpeg.execute(command);
        if (returnCode == Config.RETURN_CODE_SUCCESS) {
            return "";
        }

        String output = Config.getLastCommandOutput();
        StringBuilder message = new StringBuilder("MobileFFmpeg conversion failed");
        message.append(" rc=").append(returnCode);
        if (output != null && !output.trim().isEmpty()) {
            message.append(": ").append(output.trim());
        }
        return message.toString();
    }

    private static String audioCodec(String format) {
        if ("mp3".equals(format)) {
            return "libmp3lame";
        }
        if ("opus".equals(format)) {
            return "libopus";
        }
        if ("wav".equals(format)) {
            return "pcm_s16le";
        }
        if ("flac".equals(format)) {
            return "flac";
        }
        if ("m4a".equals(format)) {
            return "aac";
        }
        return format;
    }
}
