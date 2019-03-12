# Current results

## Betaori model

Model trying to set danger level to all 34 tiles against a player in tenpai.

### Against an open hand

The dataset contains 3,376,245 samples with open tenpai hands from the 2018 year phoenix logs. Test dataset is 675,249 (20%) samples from the 2017 year logs.

|   | Result |
| --- | --- |
| **Minimum waiting position** | 75.82% |
| Maximum waiting position | 81.94% |
| Average waiting position | 80.46% |
| Genbutsu error | 0 |

### Against a closed hand

The dataset contains 4,432,520 samples with open tenpai hands from the 2018 year phoenix logs. Test dataset is 886,504 (20%) samples from the 2017 year logs.

|   | Result |
| --- | --- |
| **Minimum waiting position** | 70.17% |
| Maximum waiting position | 79.19% |
| Average waiting position | 76.29% |
| Genbutsu error | 0 |

### Not trained model

The random prediction was run on 200,000 samples. We did it to compare how our trained model performing against pure random.

|   | Result |
| --- | --- |
| **Minimum waiting position** | 39.73% |
| Maximum waiting position | 58.55% |
| Average waiting position | 50.68% |
| Genbutsu error | 12.59 |

## Hand cost model

Model trying to predict the hand cost for tenpai player.

### Against an open hand

The dataset contains 3,376,245 samples with open tenpai hands from the 2018 year phoenix logs. Test dataset is 675,249 (20%) samples from the 2017 year logs.

|   | Result |
| --- | --- |
| Accuracy | 37.95% |
| Precision | 35.50% |
| Recall | 25.04% |
| **F1 score** | 26.23% |
| Mean square error | 1.9862 |

### Against a closed hand

The dataset contains 4,432,520 samples with open tenpai hands from the 2018 year phoenix logs. Test dataset is 886,504 (20%) samples from the 2017 year logs.

|   | Result |
| --- | --- |
| Accuracy | 32.06% |
| Precision | 22.08% |
| Recall | 15.83% |
| **F1 score** | 15.32% |
| Mean square error | 2.1410 |

### Not trained model

The random prediction was run on 886,504 samples. We did it to compare how our trained model performing against pure random.

|   | Result |
| --- | --- |
| Accuracy | 19.32% |
| Precision | 10.72% |
| Recall | 11.08% |
| **F1 score** | 10.39% |
| Mean square error | 3.8223 |


# How to set up it locally

1. `cd project`
2. `virtualenv env --python=python3`
3. `source env/bin/activate`
4. `pip install -r requirements.txt`