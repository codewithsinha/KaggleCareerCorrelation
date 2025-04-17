# KaggleCareerCorrelation

I used to wonder what is the correlation between performance and achievements on Kaggle and a career in Data Science. Does a good Kaggle profile help in real world career as a Data Scientist? So I decided to prepare datasets that would help one analyze this correlation. 

Using this project, one can have a much clear picture of the above raised question.

Steps:
1. Run "extract_kaggle_rankings_data.py" as follows:
    - python extract_kaggle_rankings_data.py competitions
    - python extract_kaggle_rankings_data.py datasets
    - python extract_kaggle_rankings_data.py notebooks
    - python extract_kaggle_rankings_data.py discussions
2. Run "extract_kaggle_users_data.py" as follows:
    - python extract_kaggle_users_data.py competitions
    - python extract_kaggle_users_data.py datasets
    - python extract_kaggle_users_data.py notebooks
    - python extract_kaggle_users_data.py discussions
3. Ensure that mongodb is running on your system with the following command: sudo systemctl status mongod
4. Run "extract_linkedin_data.py" as follows:
    - python extract_linkedin_data.py competitions
    - python extract_linkedin_data.py datasets
    - python extract_linkedin_data.py notebooks
    - python extract_linkedin_data.py discussions



Or if you just want to view the data of one specific component of Kaggle, for example datasets, you can run:
    - python extract_kaggle_rankings_data.py datasets
    - python extract_kaggle_users_data.py datasets
    - python extract_linkedin_data.py datasets
in that order.

After having completed these steps in this sequence, you will have a mongo database with the name linkedin_database which will comprise of collections having names following the format: {section}_linkedin_data (section can be replaced by either of "competitions","datasets","notebooks","discussions", whichever component's data you would have extracted)

Then you can perform various data analysis techniques on these datasets and find the answer to our question :)
