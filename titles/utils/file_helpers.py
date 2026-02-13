import io
import csv


def read_csv_file(request_file):
    file = io.StringIO(request_file.read().decode("shift-jis"))
    return csv.reader(file)
