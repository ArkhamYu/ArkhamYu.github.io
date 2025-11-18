# Created by Nadine von Frankenberg, 2025
import os
import csv
import re
import sys
import subprocess


def gather_metadata(metadata_file):
    """Reads and parses CSV file metadata"""
    try:
        with open(metadata_file, newline="") as metadata:
            metadata_reader = csv.reader(metadata, delimiter=",")
            return list(metadata_reader)
    except FileNotFoundError:
        print(f"Error: Metadata file {metadata_file} not found.")
        sys.exit(1)


def rename_files(directory):
    """Renames files = remove prefix 'text_file_XXXX-'"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if re.match(r"text_file_\d+-", file):
                new_name = re.sub(r"text_file_\d+-", "", file)
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, new_name)
                os.rename(old_path, new_path)
                print(f"Renamed: {file} -> {new_name}")


def detect_main_class(file_path):
    """Detect class with main method in a Java file"""
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            content = file.read()
            if re.search(r"public\s+static\s+void\s+main\s*\(", content):
                return os.path.basename(file_path).replace(".java", "")
    except (UnicodeDecodeError, FileNotFoundError) as e:
        print(f"Error reading file {file_path}: {e}")
    return None


def process_submission(submission_path, student_name, submitted_files, run_flag=False):
    """Rename student submission individually, run main detection/execution (optional)"""
    student_path = os.path.join(os.path.dirname(submission_path), student_name)
    os.rename(submission_path, student_path)
    print(f"Renamed folder: {submission_path} -> {student_path}")

    if not run_flag:
        # Skip all Java detection logic
        return None

    main_class = None

    for file in os.listdir(student_path):
        old_file_path = os.path.join(student_path, file)
        if re.match(r"text_file_\d+-", file):
            new_file_path = os.path.join(student_path, re.sub(r"text_file_\d+-", "", file))
            os.rename(old_file_path, new_file_path)
            print(f"Renamed: {file} -> {os.path.basename(new_file_path)}")
        else:
            new_file_path = old_file_path

        if os.path.basename(new_file_path).replace(".java", "") in submitted_files:
            detected_class = detect_main_class(new_file_path)
            if detected_class:
                main_class = detected_class

    if run_flag:
        if main_class:
            print(f"Main class detected: {main_class}")
            try:
                subprocess.run(["javac", f"{student_path}/*.java"], shell=True, check=True)
                subprocess.run(["java", "-cp", student_path, main_class], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running {main_class} for {student_name}: {e}")
        else:
            print(f"Warning: No main class detected for {student_name}!")

    return main_class


def main():
    if len(sys.argv) < 2:
        print("Usage:\n\tpython rename_folders.py [submissions_folder] [--r]")
        sys.exit(1)

    base_path = sys.argv[1]
    run_flag = "--r" in sys.argv

    metadata_file = os.path.join(base_path, "submission_metadata.csv")
    metadata = gather_metadata(metadata_file)

    for submission in os.listdir(base_path):
        if submission == "submission_metadata.csv":
            continue

        submission_path = os.path.join(base_path, submission)
        submission_number = submission[11:]
        submitted_files = []
        student_name = None
        no_submission = False

        for student in metadata[1:]:
            student_number = student[6]
            if student_number == submission_number:
                first_name = student[0]
                last_name = student[1]
                student_name = f"{first_name}_{last_name}"
                if "Missing" in student:
                    print(f"No submission for {student_name}; SKIP.")
                    no_submission = True
                else:
                    beginning = student[12].find("[{")
                    end = student[12].find("}]")
                    sub_files_str = student[12][beginning:end + 2]
                    submitted_files = sub_files_str.strip("][}{").replace(
                        'id"=>', "").replace("\"", "").replace("{", "").replace("}", "").split(", ")
                break

        if no_submission or not student_name:
            continue

        process_submission(submission_path, student_name, submitted_files, run_flag)


if __name__ == "__main__":
    main()
    