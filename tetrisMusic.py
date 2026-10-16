import math
import struct
import subprocess
import tempfile
import wave

SAMPLE_RATE = 44100
BPM = 160
BEAT = 60 / BPM
VOLUME = 0.18

# Note maps to frequency of the speakers.
# Found it online, so don't hate the player hate the game.
NOTES = {
    "E4": 329.63, "B3": 246.94, "C4": 261.63, "D4": 293.66,
    "A3": 220.00, "G3": 196.00, "F3": 174.61,
    "E5": 659.25, "D5": 587.33, "C5": 523.25, "B4": 493.88,
    "A4": 440.00, "G4": 392.00, "F4": 349.23,
    "F5": 698.46, "G5": 783.99, "A5": 880.00,
}


# Got the melody online, pretty peak.
# Note first, then the duration in beats. None is a rest.
MELODY = [
    ("E5", 1), ("B4", 0.5), ("C5", 0.5), ("D5", 1), ("C5", 0.5), ("B4", 0.5),
    ("A4", 1), ("A4", 0.5), ("C5", 0.5), ("E5", 1), ("D5", 0.5), ("C5", 0.5),
    ("B4", 1.5), ("C5", 0.5), ("D5", 1), ("E5", 1),
    ("C5", 1), ("A4", 1), ("A4", 1), (None, 1),

    (None, 0.5), ("D5", 1), ("F5", 0.5), ("A5", 1), ("G5", 0.5), ("F5", 0.5),
    ("E5", 1.5), ("C5", 0.5), ("E5", 1), ("D5", 0.5), ("C5", 0.5),
    ("B4", 1), ("B4", 0.5), ("C5", 0.5), ("D5", 1), ("E5", 1),
    ("C5", 1), ("A4", 1), ("A4", 1), (None, 1),
]

# This creates a whole, massive singular note.
def square_wave(freq, seconds):
    n = int(SAMPLE_RATE * seconds)
    samples = []

    for i in range(n):
        t = i / SAMPLE_RATE
        value = 1 if math.sin(2 * math.pi * freq * t) >= 0 else -1

        fade = min(i / 300, (n - i) / 300, 1)
        samples.append(int(value * VOLUME * 32767 * fade))

    return samples

def render_song():
    total_samples = int(sum(beats for _, beats in MELODY) * BEAT * SAMPLE_RATE)
    output = [0] * total_samples
    cursor = 0

    for note, beats in MELODY:
        length = int(beats * BEAT * SAMPLE_RATE)

        if note is not None:
            note_seconds = beats * BEAT * 0.9
            tone = square_wave(NOTES[note], note_seconds)
            output[cursor:cursor + len(tone)] = tone

        cursor += length

    return b"".join(struct.pack("<h", max(-32767, min(32767, s))) for s in output)

path = tempfile.mktemp(suffix=".wav")

with wave.open(path, "w") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)
    wav.writeframes(render_song())

subprocess.run(["afplay", path])

# numberOfTime = int(input("Enter the number of times you want to play the song: "))
# for _ in range(numberOfTime):
#     subprocess.run(["afplay", path])