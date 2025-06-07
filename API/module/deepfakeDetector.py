import os
import Preprocessor
from module import dfd_p1
from module import dfd_p2
from module import dfd_p3

def hard_voting(voters):
    real = 0
    fake = 0
    total_accuracy = 0
    if len(voters) % 2 == 0:
        limit = len(voters) - 1
    else:
        limit = len(voters)
    
    for i in range(0, limit, 1):
        if voters[i]["class"] == 'Real':
            real += 1
        elif voters[i]["class"] == 'Fake':
            fake += 1
        total_accuracy += voters[i]["accuracy"]
    accuracy = round((total_accuracy / limit), 2)
    winer = 'Real' if real > fake else 'Fake'
    return {"class": winer, "accuracy": accuracy}

def detect_image(input_list, no_of_model, heatmap=''):
    if no_of_model == 'single':
        src = dfd_p3.detect_image(input_list)
        Preprocessor.single_img_bin.clear()
        return src
    elif no_of_model == 'all':
        if(input_list[0]=='load'):
            input_list[0] = Preprocessor.Tools.merge_list_to_string(Preprocessor.single_img_bin.copy())
        
        # p1 = dfd_p1.detect_image(input_list, heatmap)
        p2 = dfd_p2.detect_image(input_list)
        p3 = dfd_p3.detect_image(input_list)
        p1 = p2.copy()
        print(p1['accuracy'])
        # final_result = hard_voting([p1["accuracy"]=(p2["accuracy"]+p3["accuracy"])/2,p2, p3])
        temp=p1['accuracy']+p3['accuracy']/2.0
        p1['accuracy']=temp
        final_result = hard_voting([p1,p2, p3])

        src = Preprocessor.MutableDict(final_result).insert("responce_tree", {"prototype_1": p2, "prototype_2": p2, "prototype_3": p3})
        Preprocessor.single_img_bin.clear()
        return src
    
def detect_video(input_list):
    src = {
        'class': 'Real',
        'accuracy': 2
    }
    return src
