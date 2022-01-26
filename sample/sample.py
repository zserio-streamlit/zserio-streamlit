import zserio
import sample.api as sample

data = sample.Data(13, "thirteen")
writer = zserio.BitStreamWriter()
data.write(writer)
print(f"serialized data: {writer.byte_array}")

reader = zserio.BitStreamReader(writer.byte_array)
read_data = sample.Data.from_reader(reader)
print(f"read_data: id={read_data.id} text: {read_data.text}")
