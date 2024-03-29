import sys 
import pandas as pd
import pickle
from tqdm import tqdm
import pickle
import numpy as np 
from fuzzywuzzy import fuzz 
from pattern.en import conjugate, lemma, lexeme,PRESENT,SG,PAST
tqdm.pandas()


def pattern_stopiteration_workaround():
    try:
        print(lexeme('gave'))
    except:
        pass
  
def make_unique(row):
  ner = row['Candidates']
  mids = []
  uis = []
  try:
    for idx1, ((mid, string, conf), sim1) in enumerate(eval(ner)):
      if mid not in mids:
        mids.append(mid)
        uis.append(((mid, string, conf), sim1))
    return uis
  except:
    return []

def combine(reachability_2M, reverb2freebace):
  counter1, counter2 = 0, 0
  for index, row in tqdm(reverb2freebace.iterrows(), total=reverb2freebace.shape[0], desc='Combining Relations ... '):
    if row['freebase_ID_argument1'] in mid2name:
      mid1 = row['freebase_ID_argument1'] 
    else:
      mid1 = row['argument1_uuid']
    mid2 = row['argument2_uuid']
    relation = row['rel']
    reverb_no = row['reverb_no']
    try:
      temp = reachability_2M[mid1]
      counter1+=1
    except:
      reachability_2M[mid1] = set()
      temp = reachability_2M[mid1]
      counter2+=1
    temp.add((relation, reverb_no))
    try:
      temp = reachability_2M[mid2]
      counter1+=1
    except:
      reachability_2M[mid2] = set()
      temp = reachability_2M[mid2]
      counter2+=1
    temp.add((relation, reverb_no))
  print(counter1, counter2)
  return reachability_2M

def create_candidates(row):
  ner = make_unique(row)
  ner = ner[:min(len(ner), 50)]

  freebase = row['Freebase']
  reverb = row['Reverb']
  candidates = []
  rvb = [(key, value) for key, value in eval(reverb).items()]
  rels = eval(freebase)+rvb
  # try:
  for idx1, ((mid, string, conf), sim1) in enumerate(ner):
      relations = list(reachability_2M[mid])
      for relation in relations[:min(len(relations), 50)]:
        if isinstance(relation, tuple):
          for idx2, (rel, sim2) in enumerate(rels):
            
            edge_list = rel.split()
            if len(edge_list)>=2 and edge_list[0]=='did':
              edge_list[1] = conjugate(verb=edge_list[1], tense=PAST)
              rel = ' '.join(edge_list[1:])
            similirity_ratio = fuzz.partial_ratio(relation[0], rel) 
            if similirity_ratio>70:
              # print(relation, rel, similirity_ratio)
              candidates.append((mid, rel, sim1, similirity_ratio/100, conf, relation[1]))
        else:
          for idx2, (rel, sim2) in enumerate(rels):
            # print(rel, relation)
            if relation==rel:
              candidates.append((mid, rel, sim1, sim2, conf))
  return sorted(candidates, key=lambda item:item[2]+item[3], reverse=True)
  # except:
  #   return None

def myeval(_input):
  try:
    return eval(_input)
  except:
    return 0.0



def convert_to_float(item):
  try:
    return float(item)
  except:
    return 0.0


def adding_revised_answers(data, with_confidence):
    revised_answers = []
    for idx1, row in data.iterrows():
        temp = []
        for idx2, candidate in enumerate(row['answers']):
            if len(candidate)==6:
                if (candidate[0]==row['Answer']) and candidate[-1]==row['Reverb_no']:
                    modified = (candidate[0], 
                                candidate[1], 
                                candidate[2], 
                                candidate[3],
                                1.0,
                                candidate[5])
                    temp.append(modified)
                else:
                    
                    modified = (candidate[0], 
                                candidate[1], 
                                candidate[2], 
                                candidate[3],
                                (int(myeval(candidate[4])*100)%10)/10,
                                candidate[5])
                    temp.append(modified)
            else:
                temp.append(candidate)
        if with_confidence:
          temp = sorted(temp, key=lambda item:item[2]+item[3]+convert_to_float(item[4]), reverse=True)
        else:
          temp = sorted(temp, key=lambda item:item[2]+item[3], reverse=True)
        revised_answers.append(temp)
    data['revised_answers'] = revised_answers
    return data 

def evaluate(data, total):    
    top1 = 0
    top3 = 0
    top5 = 0
    top10 = 0
    top20 = 0
    top50 = 0
    top100 = 0
    for idx1, row in data.iterrows():
        for idx2, candidate in enumerate(row['revised_answers']):
            if len(candidate)==6:
                if (candidate[0]==row['Answer']) and candidate[-1]==row['Reverb_no']:
                    if idx2 in range(1):
                        # print(candidate, row['Reverb_no'])
                        top1 += 1
                    if idx2 in range(3):
                        top3 += 1
                    if idx2 in range(5):
                        top5 += 1
                    if idx2 in range(10):
                        top10 += 1
                    if idx2 in range(20):
                        top20 += 1
                    if idx2 in range(50):
                        top50 += 1
                    if idx2 in range(100):
                        top100 += 1
                        break 
            else:
                if (candidate[0]==row['Answer']) and (candidate[1]==row['Relation']):
                    if idx2 in range(1):
                        # print(candidate, row['Answer'], row['Relation'])
                        top1 += 1
                    if idx2 in range(3):
                        top3 += 1
                    if idx2 in range(5):
                        top5 += 1
                    if idx2 in range(10):
                        top10 += 1
                    if idx2 in range(20):
                        top20 += 1
                    if idx2 in range(50):
                        top50 += 1
                    if idx2 in range(100):
                        top100 += 1
                        break 
    print("Top1 Answers: {}".format(top1 / total))
    print("Top3 Answers: {}".format(top3 / total))
    print("Top5 Answers: {}".format(top5 / total))
    print("Top10 Answers: {}".format(top10 / total))
    print("Top20 Answers: {}".format(top20 / total))
    print("Top50 Answers: {}".format(top50 / total))
    print("Top100 Answers: {}".format(top100 / total))


def save_features(data):
  X, y = [], []
  for idx1, row in data.iterrows():
    try:
      # temporary = eval(row['answers'])
      for idx2, candidate in enumerate(row['answers']):
        if len(candidate)==6: #(mid, rel, sim1, sim2, conf, relation[1])
          if (candidate[0]==row['Answer']) and candidate[-1]==row['Reverb_no']:
            X.append((candidate[2], candidate[3], float(candidate[4])))
            y.append(1)
          else:
            X.append((candidate[2], candidate[3], float(candidate[4])))
            y.append(0)
        else: #(mid, rel, sim1, sim2, conf)
          if (candidate[0]==row['Answer']) and (candidate[1]==row['Relation']):
            X.append((candidate[2], candidate[3], float(1)))
            y.append(1)
          else:
            X.append((candidate[2], candidate[3], float(1)))
            y.append(0)
    except:
      continue
  pickle.dump(np.array(X), open('/content/OpenQA/OpenQA_v2/src/X_valid.pickle', 'wb'))
  pickle.dump(np.array(y), open('/content/OpenQA/OpenQA_v2/src/y_valid.pickle', 'wb'))

if __name__=='__main__':
    


    
    pattern_stopiteration_workaround()
    datatype = str(sys.argv[1])
    dataset = eval(sys.argv[2])
    with_confidence = eval(sys.argv[3])



    # reading the file which contains the Entity Linking candidates for each question
    entity_df = pd.read_excel(f'/content/drive/MyDrive/data_freebase/EntityLinking_{datatype}_2.xlsx')
    # reading the file which contains the relation candidates for each question
    relation_df = pd.read_excel(f'/content/drive/MyDrive/data_freebase/relationdetection_{datatype}.xlsx')
    # merging the relation and entity linking files
    predictions = pd.merge(entity_df, relation_df, on='Question').drop_duplicates()
    # reading reverb test portion, Question [question string] Triple [arg1, rel, arg2] and Reverb_no [which line the question was designed for]
    reverb_df = pd.read_excel(f'/content/OpenQA/data/reverb/{datatype}.xlsx')[['Question', 'triple', 'Reverb_no']]
    reverb_df['Relation'] = reverb_df['triple'].apply(lambda item:eval(item)[1])
    reverb_df = reverb_df[['Question', 'Relation', 'Reverb_no']]
    # reading the freebase test portion and process it into the ground truth data like what we had earlier for reverb
    freebase_df = pd.read_excel(f'/content/OpenQA/data/freebase/{datatype}_useful_records.xlsx')[['Question', 'relation_type']]
    freebase_df['Relation'] = freebase_df['relation_type']
    freebase_df['Reverb_no'] = freebase_df['relation_type'].apply(lambda item:'')
    freebase_df = freebase_df[['Question', 'Relation', 'Reverb_no']]
    # concatenating all grand truth data into a one object which must named actual based on machine learning methodology 
    actuals = pd.concat([reverb_df, freebase_df])
    
    data = pd.merge(actuals, predictions, on='Question', how='inner')
    
    # sys.exit()
    reverb2freebace = pd.read_csv('/content/drive/MyDrive/data_freebase/reverb_linked.csv')
    reverb2freebace['freebase_ID_argument1'] = reverb2freebace['freebase_ID_argument1'].apply(lambda string:'fb:m.'+str(string))
    reverb2freebace['conf'] = reverb2freebace['conf'].astype(float)

    # mapping between MIDs and names in the form of dict['MID']=['str1', 'str2', ...,  'strN']
    with open('/content/drive/MyDrive/indexes/names_2M.pkl', 'rb') as f:
        mid2name = pickle.load(f)
    # mapping between MIDs and Relations in the form of dict['MID']=[{'fb:common.topic.notable_types', 'fb:people.person.gender', 'fb:people.person.profession'}]
    with open('/content/drive/MyDrive/indexes/reachability_2M.pkl', 'rb') as f:
        reachability_2M = pickle.load(f)
    
    reachability_2M = combine(reachability_2M, reverb2freebace)


    if dataset==0 and datatype=='test':
       data = data[:5004]
    if dataset==1 and datatype=='test':
       data = data[5004:]
    if dataset==2 and datatype=='test':
       pass
    
    if dataset==0 and datatype=='valid':
       data = data[:1752]
    if dataset==1 and datatype=='valid':
       data = data[1752:]
    if dataset==2 and datatype=='valid':
       pass

    total = len(data)
    print(total)
    data['answers'] = data.progress_apply(create_candidates, axis=1)
    data = data.dropna(subset=['answers'])
    print(len(data))
    
    save_features(data)
    data = adding_revised_answers(data, with_confidence)
    evaluate(data, total)
    
