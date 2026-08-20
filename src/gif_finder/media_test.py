from PIL import Image

path = "/Users/demolaze/clips/aug_10/gifs/raid_muzz_test.webp"

with Image.open(path) as image:
    print("format:", image.format)
    print("size:", image.size)
    print("mode:", image.mode)
    print("n_frames:", image.n_frames)
    print("info:", image.info)

    for i in range(min(image.n_frames, 10)):
        image.seek(i)
        print(
            f"frame {i}:",
            "size=",
            image.size,
            "duration=",
            image.info.get("duration"),
            "timestamp=",
            image.info.get("timestamp"),
        )
