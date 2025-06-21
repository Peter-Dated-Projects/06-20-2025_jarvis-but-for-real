import pickle


filename = "whispercpp-audio-test.save"

# load data with pickle
data = pickle.load(open(filename, "rb"))

# get each chunk
_header = data["header"]
print(_header)
print()

_audio_chunks = data["audio_chunks"]
print(f"Audio Chunk Count: {_audio_chunks['count']}")
for i in range(len(_audio_chunks["chunks"])):
    print(f"Audio Chunk {i}:")
    print(_audio_chunks["chunks"][i])
    print()
print()

_segment_data = data["segment_data"]
# unpickle each segment
for i in range(len(_segment_data["segments"])):
    _segment_data["segments"][i] = pickle.loads(_segment_data["segments"][i])

print(f"Segment Count: {len(_segment_data['segments'])}")
for i in range(len(_segment_data["segments"])):
    print(f"Segment {i}:")
    print(_segment_data["segments"][i])
    print()
