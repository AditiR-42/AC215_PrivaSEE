# AC215 - Milestone4 - PrivaSee

**Team Members** Glo Umutoni, Shira Aronson, Aditi Raju, Sammi Zhu, Yeabsira Mohammed

**Group Name** PrivaSee

------------------------
### Milestone4
In this milestone, we have the components for frontend, API service, and components from previous milestones for data management, versioning, and language models.

After building a ML Pipeline in our previous milestone, we have built a backend api service and frontend app. This will be our user-facing application that ties together the various components built in previous milestones.

**Application Design** 

We designed both a Solution Architecture and a Technical architecture to ensure all components of our app work together. 

Here is our Solution Architecture:

<img src="images/solution-arch.png"  width="800">

Here is our Technical Architecture:

<img src="images/technical-arch.png"  width="800">

**Backend API** 

We used fast API to build the backend service. This exposes the model functionality to the frontend.

**Frontend** 

A React app was built to identify privacy issues in terms and conditions using a trained Gemini model on the backend. On the app, a user can upload terms and conditions and receive a summary of key issues and a privacy grade: the app sends the pdf to the backend api to get classification results. Additionally, a user can request app recommendations using natural language. The application components consist of the home page, authorization, pdf summarization, and app recommendation. On the backend, there are routes for both the pdf summarization/grading API as well as the app recommendation API (using a chat interface). 

For now, running the React app locally requires installing modules listed in `requirements.txt` and `npm-requirements.txt`. These setup requirements will be containerized and abstracted away from the user once the website is deployed.

To actually run the React app locally, there are two steps: 

1. In `src`:
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

Here are some screenshots of our app:
<img width="800" alt="Screenshot 2024-11-19 at 5 47 33 AM" src="https://github.com/user-attachments/assets/b1aa8eb9-1fd7-49f7-8b13-c49ca58d7bbc">
<img width="800" alt="Screenshot 2024-11-19 at 5 06 51 PM" src="https://github.com/user-attachments/assets/bea04d22-947d-4f4c-90e3-ecc8ae6033bb">
<img width="800" alt="Screenshot 2024-11-19 at 5 47 47 AM" src="https://github.com/user-attachments/assets/1f19a728-64ef-46ca-a237-71316927b903">
<img width="800" alt="Screenshot 2024-11-19 at 5 08 15 PM" src="https://github.com/user-attachments/assets/39be97bc-891e-4855-9fc9-06c5d561c666">
<img width="800" alt="Screenshot 2024-11-19 at 5 47 57 AM" src="https://github.com/user-attachments/assets/0cea299c-3a5d-4600-b647-d963aba55265">
<img width="800" alt="Screenshot 2024-11-19 at 5 09 12 PM" src="https://github.com/user-attachments/assets/3777277a-b74b-4898-9445-1dc6a522ffb0">

**Automated Testing** 

Our project uses a combination of unit and integration tests to validate individual functions and the interaction between components. External dependencies, such as Google Cloud Storage and Vertex AI, are mocked to ensure tests are isolated and do not rely on external systems. Test coverage is measured using `pytest-cov` to ensure critical code paths are adequately tested. 

Testing Tools Used:
- **PyTest**: Used for writing and running test cases.
- **PyTest-Cov**: used for measuring test coverage.
- **Unittest.mock**: used for mocking library for isolating code during tests.

To Test Locally:
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
2. **Run all tests**:
    ```bash
    pytest --cov=. --cov-report=html
3. **Run specific tests**:
    ```bash
    pytest src/models/tests/test_issues.py

#### Running Docker
To run Dockerfile in either container, make sure to be in `/src/desired-container`:

1. Run the command `bash docker-shell.sh`
2. When set ran correctly, you should expect to see the following as demonstrated in the screenshot.
![Image](reports/docker-screenshot.png)


### Notebooks/Reports
Both folders here contains code that is not part of the container. Notebooks contains the original `.ipynb` files used to run the code, however, are also converted into `.py` files in the containers. Reports contains the write up from previous milestones. 

### Midterm Presentation
Filename: midterm_presentation/PrivaSee_Midterm.pdf

### Deployment
[insert writeup if we need one]
As part of our scaling using Kubernetes, we used the script at src/deployment/scaling-test.py to ensure that autoscaling was effective. While the small size of each request made it difficult to increase memory to the point where new clusters were needed. However, the test nevertheless showed that scaling was enabled and that the site was able to accommodate significant request traffic. (see the screenshots in the images folder for these results)
