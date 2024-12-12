# AC215 2024 PrivaSee 
[Medium Article](https://medium.com/institute-for-applied-computational-science/privasee-the-ml-architecture-transforming-privacy-policy-understanding-a64e6bb40097) [Video Walkthrough](https://drive.google.com/file/d/1xhDB6TqIIWHjfAjVfUn1ziyXZJW_Igo1/view)

**Team Members** Glo Umutoni, Shira Aronson, Aditi Raju, Sammi Zhu, Yeabsira Mohammed

**Group Name** PrivaSee

**Project** Project When deciding on a messaging app, for example, the average consumer is unlikely to read or understand the terms and conditions of multiple apps and decide which one to use accordingly. This project aims to bridge consumers’ knowledge gaps around their data privacy by building an app that reviews terms and conditions agreements and informs users about the aspects of the privacy they cede by using a certain app or website. PrivaSEE would allow users to understand the implications to their data privacy, and compare options in a way that aligns with their personal privacy priorities.

## Project Organization
See below for the organizational structure of the project. Containerizations are elaborted upon (note that Dockerfiles and additional bashscripts and pyenv files exist but have been omitted from overview for brevity). Additional files can be found in the codebase directory. 
```
├── midterm_presentation
├── notebooks
├── reports
└── src
    ├── api-service/
    │   ├── api/
    │   │   ├── routers
    │   │   ├── utils
    │   ├── service.py
    ├── datapipeline/
    │   ├── clean_data_for_recommendations.py
    │   ├── clean_data.py
    │   ├── create_gemini_tuning_datasets.py
    │   ├── create_vertexai_datasets.py
    │   ├── get_data_for_recommendations.py
    │   └── scraping_prototype.py
    ├── deployment/
    ├── frontend-react/
        │   ├── public/
        │   ├── src/
        │   │   ├── app/
        │   │   │   ├── about/
        │   │   │   ├── recommend/
        │   │   │   ├── summarize/
        │   │   │   ├── auth.js
        │   │   │   ├── global.css
        │   │   │   ├── layout.jsx
        │   │   │   ├── page.jsx
        │   │   ├── components/
        │   │   │   ├── auth/
        │   │   │   ├── chat/
        │   │   │   ├── home/
        │   │   │   ├── layout/
        │   │   ├── services/
        │   │   │   ├── Common.js/
        │   │   │   ├── DataService.js/
    ├── models
    │   ├── tests/
    │   ├── category_weights.csv
    │   ├── get_issues.py
    │   ├── modeling_functions.py
    │   ├── multi_class_model.py
    │   └── privacy_grader.py
    └── workflow
├── LICENSE
├── README.md
```

## Prerequisites and Setup Instructions
Please see below on different methods to set up and run the application. General packages used are also listed as in `requirements.txt` for ease of comparison with user's local package versions. However, this step is truly optional as the Dockerfile is configured via Pipfile to install the same dependices. 

### Running Docker
To run Dockerfile in either container, make sure to be in `/src/desired-container`:

1. Run the command `bash docker-shell.sh`
2. When set ran correctly, you should expect to see the following as demonstrated in the screenshot.
![Image](reports/images/docker-screenshot.png)

### Running Project Locally
1. In `src`: (optional depending on local configuration):
   ```
   pip install -r requirements.txt
2. In `src/frontend-react`: 
   ```bash
   npm install
   npm run dev   
3. In `src/api_service`:
   ```bash
   uvicorn api.service:app --reload --host 0.0.0.0 --port 9000
If issues arise, check that `npm --version = 10.8.3` and `nvm --version = 22.9.0`

### CI/CD Pipeline Implementation and Testing:
We implemented CI/CD Pipeline and Testing through Github Actions. The workflow files for automated deployment can be found in `.github/workflows` and `src/deployment`. Please see the following screenshots for automated deployment verification.

1. Github Actions Overview
![Image](reports/images/deploy_overview.JPG)

2. Deployment In Progress
![Image](reports/images/deployment%201.JPG)
![Image](reports/images/deployment%202.JPG)

3. Deployment Success
![Image](reports/images/successful_deploy.JPG)

We wrote tests to cover model logic in `src/models` as well as API endpoints for summarize and recommend functionalites in `src/api_service`. Tests can be found in `src/models/tests`. Please see the following screenshots for testing verification.

1. Running Tests
<img width="1497" alt="Screenshot 2024-12-11 at 10 21 48 PM" src="https://github.com/user-attachments/assets/52494948-8ba9-40ff-a4d3-e6e27d4913c3" />

2. Uploading Test Coverage
<img width="1497" alt="Screenshot 2024-12-11 at 10 22 07 PM" src="https://github.com/user-attachments/assets/22acbb65-0381-4ef7-88fb-3c48dc343aed" />

3. Test Coverage (71%)
<img width="1497" alt="Screenshot 2024-12-11 at 10 26 26 PM" src="https://github.com/user-attachments/assets/91363a6d-2dee-438c-a46d-79556f005285" />
<img width="1497" alt="Screenshot 2024-12-11 at 10 27 02 PM" src="https://github.com/user-attachments/assets/3431baa9-257f-4fd8-a7c0-11d3f7358845" />

As shown above, our tests cover 71% of our code, including every file related to model logic and every file related to API services. However, we can still increase testing for specific functions. In `recommend.py`, we can increase testing for `find_best_genre_match_with_gemini`. In `summarize.py`, we can increase testing for `get_grade`. In `privacy_grader.py`, we can increase testing for `create_case_mappings` and `create_category_mappings`. In `process_pdf.py`, we can increase testing for `extract_text_from_pdf`. Besides these functions, our tests cover the main functionality of `recommend`, `summarize`, `privacy_grader`, and `process_pdf`, in addition to model logic.

## Deployment Instructions
Note: The following provides an overview of the setup steps. `.yml` and `Dockerfiles` files can be found in `src/deployment`. For exact steps on what code to run, please visit [here](https://github.com/dlops-io/cheese-app-v3/blob/main/README.md).

### Deployment with Ansible (GCP Virtual Machine)
Run these commands:

1. ansible-playbook deploy-docker-images.yml -i inventory.yml
2. ansible-playbook deploy-create-instance.yml -i inventory.yml --extra-vars cluster_state=present
3. ansible-playbook deploy-provision-instance.yml -i inventory.yml
4. ansible-playbook deploy-setup-containers.yml -i inventory.yml
5. ansible-playbook deploy-setup-webserver.yml -i inventory.yml
6. ansible-playbook deploy-create-instance.yml -i inventory.yml --extra-vars cluster_state=absent

---

### Deployment with Scaling (Kubernetes)
Run these commands:

1. ansible-playbook deploy-docker-images.yml -i inventory.yml
2. ansible-playbook deploy-k8s-cluster.yml -i inventory.yml --extra-vars cluster_state=present


See screenshots below for reference of what scaling verfication should look like on GCP after completion:
![Image](reports/images/scaling%20screenshot%201.png)
![Image](reports/images/scaling%20screenshot%202.png)


## Usage Details and Examples
A React app was built to identify privacy issues in terms and conditions using a trained Gemini model on the backend. The Homepage (shown below) showcases the functionalities of the application and serves as the guide to other pages. 

![Image](reports/images/homepage.png)


There are two core functionalities:
### `Summarize:` 
1. Users choose any file from their laptop to upload. 
![Image](reports/images/summarize.png)

2. Once loaded, users are given the option to upload their file to the web-application. 
![Image](reports/images/file_loaded.png)

3. A loading bar indicates to users the status of their file loading. Once successfully loaded, users can fetch for a grade.
![Image](reports/images/file_load_bar.png)

4. The retrieved data returned maps the privacy issues to one of 22 privacy components (i.e. privacy, governance, etc) along with the overall privacy grade. Bars highlight the counts of various privacy components and the tables provide more description of the specific violations.
![Image](reports/images/summarize_results.png)

### `Recommend:` 
1. Users can use the chatbox to ask for a genre or an app similar to another app, along with the privacy concerns they want the app to be aware of. 
![Image](reports/images/recommend.png)
![Image](reports/images/user_prompt.png)

2. A load spin appears while the backend retrieves the output response from the model.
![Image](reports/images/rec_load.png)

3. The final results are outputed in a chat div format for readers to see what app the model recommended. 
![Image](reports/images/recommend_results.png)

Additionally, there is also an `About` page that further describes the goals of our web application. 
![Image](reports/images/about.png)

## Known Issues and Limitations

### Model Robustness
Despite setting a consistent temperature parameter to control the randomness of outputs, the model’s responses occasionally lack robustness. This can result in less robust outputs. Further fine-tuning or additional constraints might be required to enhance reliability across all use cases.

### File Upload Time
The time required to upload a file is directly proportional to its size. Larger files, especially those exceeding several megabytes, can result in noticeable delays, potentially impacting user experience. Optimizations in file handling or upload infrastructure could help mitigate this issue in future iterations.

### Variable Model Response Time
The response time for generating outputs from the model can vary depending on the complexity of the input query and server load. While most queries are resolved in a few seconds, users may occasionally experience delays (up to 15 seconds or more).
