#!/bin/bash
#conda activate rapids WRONG
source /home/rockwell/miniconda3/bin/activate rockwell_deploy #correct
#python Documents/my_python_file_name.py WRONG SEPARATLY GO TO FOLER WHTAN EXECUTE EITH python
#cd ~/Documents/folder_where_python_file_is/ #correct
#python /home/rockwell/Rockwell/backend/src/recsys/scripts/recsys_surprise_training_cronjob.py /home/rockwell/Rockwell/backend/src #correct
python /home/rockwell/Rockwell/backend/src/recsys/scripts/recsys_surprise_prediction_cronjob.py /home/rockwell/Rockwell/backend/src
conda deactivate
