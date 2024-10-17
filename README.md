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

**Model Container** Glo/Yeab

### Data Pipeline Overview
1. `src/datapipeline/scraping_prototype.py` This script is a web scraping prototype from the ToS;DR dataset. It processes pre-annotated information done by the API regarding various cases, their terms and conditions, the corresponding ratings, and etc. The preprocessed information has been cleaned and condensed for easier model training. 
2. `/src/datapipeline/Pipfile` This file contains the various packages needed to help with preprocessing.
3. `src/datapipeline/Dockerfile` Our Dockerfile follow standard conventions. More information on how to run the docker file can be followed below in virtual environment setup. 
4. `src/datapipeline/docker-compose.yaml` This yaml file supports the docker-shell-compose.sh script. 
5. `src/datapipeline/docker-shell-compose.sh` The shell script ensures that the data-pipeline network is created if it doesn’t already exist, builds the Docker image from the Dockerfile, and uses docker-compose to run the data-pipeline-cli service defined in the docker-compose.yaml
6. `src/datapipeline/docker-shell.sh` This script creates a custom network, builds a custom-label-studio Docker image, and resets existing containers to ensure a fresh setup.

### Model Overiew
1. `/src/models/Pipfile` This file contains the various packages needed to help with preprocessing.
2. `src/models/Dockerfile` Our Dockerfile follow standard conventions. More information on how to run the docker file can be followed below in virtual environment setup. 
3. Sammi add in more info after glo gives the files!!

### Versioned Data Strategy
Data versioning is maintained on GCP through different folder categorization. The various folders keep track of where the scraped and clean data are, along with which we will be using for various stages of our work. Currently, most of the work is being done with data found under the `tosdr-data` folder, and the `opp115_data` folder holds data that will be useful in future milestones. 
```
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
To run Dockerfile in both the datapipeline container and the models container:
1. Run the command `bash docker-shell-compose.sh`
2. When set ran correctly, you should expect to see the following as demonstrated in the screenshot.
![Image](reports/docker-screenshot.png)

### Notebooks/Reports
Both folders here contains code that is not part of the container. Notebooks contains the original `.ipynb` files used to run the code, however, are also converted into `.py` files in the containers. Reports contains the write up from previous milestones. 