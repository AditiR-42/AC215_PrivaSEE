# AC215 - Milestone2 - PrivaSee

**Team Members** Glo Umutoni, Shira Aronson, Aditi Raju, Sammi Zhu, Yeabsira Mohammed

**Group Name** PrivaSee

**Project** When deciding on a messaging app, for example, the average consumer is unlikely to read or understand the terms and conditions of multiple apps and decide which one to use accordingly. This project aims to bridge consumers’ knowledge gaps around their data privacy by building an app that reviews terms and conditions agreements and informs users about the aspects of the privacy they cede by using a certain app or website. PrivaSEE would allow users to understand the implications to their data privacy, and compare options in a way that aligns with their personal privacy priorities.

## Milestone2
In this milestone, we have the components for data management, including versioning, as well as the initial model training data. 

**Data** We gathered a dataset of approximately 30,000 annotations by ToS;DR. Each annotation includes the referenced document, the specific text the annotator addressed, and the privacy issues raised. The dataset is approximately 1GB in size and stored in a private Google Cloud bucket.

**Data Pipeline Containers** 
1. One container scrapes the ToS;DR annotation to obtain the 1GB dataset that we use for further model training. CSV files with various attributes (i.e. annotations, terms and condition documents, grades, etc) stored in the specified GCS location. For more specification, view the layout in `Versioned Data Strategy`. 
2. The other container cleans the original raw data scraped, where the updated CSV datasets are stored in GCP as well. 

**Model Container** 
The Model Container operates within our GCP architecture, specifically designed to train, validate, and deploy the machine learning models using the cleaned and processed datasets provided by the Data Pipeline Containers.  This contains the model training feature.

Model Training: Utilizes the latest cleaned datasets stored in GCP from the Data Pipeline Containers to train our BERT base model.

### Data Pipeline Overview
In this milestone, we worked on updating our model training approach and proceeded to start fine-tuning data. 
1. `src/datapipeline/clean_data.py` *New* This script performs data cleaning operations, including HTML tag removal and URL filtering, and provides functions to upload or read datasets from GCP.
2. `src/datapipeline/create_gemini_tuning_datasets.py` *New* This script prepares datasets for Gemini model tuning by processing privacy-related CSV data, generating JSONL files, and uploading them to GCP.
3. `src/datapipeline/create_vertexai_datasets.py` *New* This script generates training, validation, and testing datasets in JSONL format for Vertex AI, using grouped and labeled privacy issue data from a CSV, and uploads them to GCP. 
4. `src/datapipeline/data_cleaning_functions.py` This script cleans the data scrapped from the scraping prototype. 
5. `src/datapipeline/docker-compose.yaml` This yaml file supports the docker-shell-compose.sh script. 
6. `src/datapipeline/docker-shell.sh` This script creates a custom network, builds a custom-label-studio Docker image, and resets existing containers to ensure a fresh setup.
7. `src/datapipeline/Dockerfile` Our Dockerfile follow standard conventions. More information on how to run the docker file can be followed below in virtual environment setup. 
8. `/src/datapipeline/Pipfile` This file contains the various packages needed to help with preprocessing.
9. `src/datapipeline/retrieving_opp215_data.py` This is a placeholder file for work we will do next milestone. 
10. `src/datapipeline/scraping_prototype.py` This script is a web scraping prototype from the ToS;DR dataset. It processes pre-annotated information done by the API regarding various cases, their terms and conditions, the corresponding ratings, and etc. The preprocessed information has been cleaned and condensed for easier model training. 

### Model Overiew
1. `src/datapipeline/docker-shell.sh` This script creates a custom network, builds a custom-label-studio Docker image, and resets existing containers to ensure a fresh setup.
2. `src/models/Dockerfile` Our Dockerfile follow standard conventions. More information on how to run the docker file can be followed below in virtual environment setup. 
3. `/src/models/modeling_functions.py` Includes reusable modeling functions that are used across various modeling stages. These functions are geared towards setting up data structures for training, including data loaders and custom PyTorch datasets, and operationalizing the training loop and evaluation metrics.
4. `/src/models/multi_class_model.py`Includes the definition of the `PrivacyDataset` class for handling data loading and preprocessing, including text chunking to fit within BERT’s maximum sequence length, and a custom `collate_fn` to handle batches of data.
5. `/src/models/Pipfile` This file contains the various packages needed to help with preprocessing.

### Versioned Data Strategy
Data versioning is maintained on GCP through different folder categorization. The various folders keep track of where the scraped and clean data are, along with which we will be using for various stages of our work. In milestone2, most of the work was completed in the `legal-terms-data` bucket. In this milestone, we did finetuning of our dataset, along with utilizing a new training platform, Vertex AI, due to limitations from previous models. 
```
├── cloud-ai-platform-9509774c-e619-4d85-a500-b2179d109f91/
    ├── dataset-2466856041741025280/
    │   ├── preprocessed_examples/    
    ├── dataset-3605703797512339456/
    │   ├── preprocessed_examples/    
    ├── prompt-data/
├── legal-terms-data/
    ├── opp115_data/
    │   ├── clean/
    │   ├── raw/
    │   │   ├── annotations/        
    │   │   ├── consolidation/ 
    │   │   ├── documentation/ 
    │   │   ├── original_policies/    
    │   │   ├── pretty_print_uniquified/ 
    │   │   ├── pretty_print/
    │   │   ├── sanatized polices/          
    ├── tosdr-data/
    │   ├── clean/
    │   ├── modeling/
    │   ├── raw/
    │   │   ├── intermediate_data_files/ 
   
```

### Mock-up of the Application
Please see the attached [link](https://www.figma.com/proto/2vH2YvNCwrQwaWzuAyjBRf/Untitled?node-id=1-8&node-type=canvas&t=zR7ESBDVrApvzAjv-1&scaling=scale-down&content-scaling=fixed&page-id=0%3A1) for the Figma prototype.

### Virtual Environment Setup
Virtual environment is set up in Docker, ensuring smoother dependency management, isolation of libraries, and consistent execution across different systems.
#### Running Docker 
To run Dockerfile in the datapipeline container, make sure to be in `/src/datapipeline`::
1. Run the command `bash docker-shell.sh`
2. When set ran correctly, you should expect to see the following as demonstrated in the screenshot.
![Image](reports/docker-screenshot.png)

To run Dockerfile in the models container, make sure to be in `/src/models`:
1. Run the command `bash docker-shell.sh`
2. When set ran correctly, you should expect to see the following as demonstrated in the screenshot.
![Image](reports/models-docker.png)

### Notebooks/Reports
Both folders here contains code that is not part of the container. Notebooks contains the original `.ipynb` files used to run the code, however, are also converted into `.py` files in the containers. Reports contains the write up from previous milestones. 

### Midterm Presentation
Filename: midterm_presentation/PrivaSee_Midterm.pdf
