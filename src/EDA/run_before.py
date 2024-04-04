import os
# from patient note to summarized output using baseline

# ZERO. Convert \n to Space
def _replace_newline(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    for i in range(9, len(lines)):
        lines[i] = lines[i].rstrip('\n') + ' '
    with open(filename, 'w') as file:
        file.writelines(lines)
def replace(PAT_NOTE_DIR):
    for folder in os.listdir(PAT_NOTE_DIR):
        if os.path.isdir(os.path.join(PAT_NOTE_DIR, folder)):
            for filename in os.listdir(os.path.join(PAT_NOTE_DIR, folder)):
                file_path = os.path.join(PAT_NOTE_DIR, folder, filename)
                _replace_newline(file_path)

# ONE. From Patient Note to Unsummarized Baseline Output

# TWO.Add Lookup Dict

# THREE. From Unsummarized Output to Patient Level

# FOUR. Add Empty Patient Pair

# Five. Eval

def main(PAT_NOTE_DIR):
    replace(PAT_NOTE_DIR) 

if __name__ == "__main__":
    DIR_LST = [
        "/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/input/change_n2space/input_breast_train/Patient_Notes/breast/train",
        "/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/input/change_n2space/input_melanoma_train/Patient_Notes/melanoma/train",
        "/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/input/change_n2space/input_ovarian_train/Patient_Notes/ovarian/train"
    ] 
    for PAT_NOTE_DIR in DIR_LST:
        main(PAT_NOTE_DIR)