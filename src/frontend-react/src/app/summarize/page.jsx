"use client";

import React, { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import DataService from "../../services/DataService";
import styles from "./styles.module.css";

import "react-pdf/dist/esm/Page/TextLayer.css";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";

// Use a CDN for the worker to avoid local path issues
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

export default function FileUploadPage() {
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfFileName, setPdfFileName] = useState(null);
  const [pdfData, setPdfData] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [grade, setGrade] = useState(null);
  const [issues, setIssues] = useState([]);
  const [isUploadDisabled, setUploadDisabled] = useState(false);
  const [isFetchDisabled, setFetchDisabled] = useState(true);
  const [message, setMessage] = useState(""); // New state for displaying messages

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (file && file.type === "application/pdf") {
      setPdfFile(file);
      setPdfFileName(file.name); // Update file name
      const reader = new FileReader();
      reader.onload = (e) => setPdfData(e.target.result);
      reader.readAsArrayBuffer(file);
      setMessage(""); // Clear message when a new file is selected
    } else {
      setMessage("Please upload a valid PDF file.");
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  const handleUpload = async () => {
    if (!pdfFile) {
      setMessage("Please upload a PDF file first.");
      return;
    }

    try {
      setUploadProgress(10);
      const projectId = "473358048261";
      const locationId = "us-central1";
      const endpointId = "5609779793168957440";

      const response = await DataService.UploadFiles(
        pdfFile,
        null,
        projectId,
        locationId,
        endpointId
      );
      console.log("Upload response:", response);
      setUploadProgress(100);
      setIssues(response.found_issues);
      setMessage("PDF processed successfully. You can now fetch the grade.");
      setFetchDisabled(false);
      setUploadDisabled(true);
    } catch (error) {
      console.error("Error uploading PDF:", error);
      setMessage("Failed to process files.");
    }
  };

  const handleFetchGrade = async () => {
    try {
      setUploadDisabled(true); // Disable Upload PDF button
      const response = await DataService.GetGrade();
      console.log("Grade response:", response);
      setGrade(response);
      setMessage("Grade fetched successfully!");
    } catch (error) {
      console.error("Error fetching grade:", error);
      setMessage("Failed to fetch grade.");
      setUploadDisabled(false); // Re-enable Upload PDF button if fetching fails
    }
  };

  return (
    <div className={styles.container}>
    {pdfData ? (
        <div className={styles.layout}>
        {/* Left Column */}
        <div className={styles.viewerColumn}>
            <div className={styles.viewer}>
            <Document
                file={pdfData}
                onLoadSuccess={onDocumentLoadSuccess}
                className={styles.pdfDocument}
            >
                <Page pageNumber={pageNumber} />
            </Document>
            <p>
                Page {pageNumber} of {numPages}
            </p>
            <div className={styles.navigation}>
            <button
                onClick={() => setPageNumber((prev) => Math.max(prev - 1, 1))}
                disabled={pageNumber <= 1}
                className={styles.navButton}
            >
                ←
            </button>
            <button
                onClick={() => setPageNumber((prev) => Math.min(prev + 1, numPages))}
                disabled={pageNumber >= numPages}
                className={styles.navButton}
            >
                →
            </button>
            </div>
            </div>
        </div>

        {/* Right Column */}
        <div className={styles.controlColumn}>
            <div className={styles.fileInputs}>
            <label htmlFor="pdfUpload" className={styles.label}>
                PDF File (Terms and Conditions):
            </label>

            <div className={styles.customFileContainer}>
                <input
                type="file"
                id="pdfUpload"
                accept=".pdf"
                className={styles.hiddenFileInput}
                onChange={handleFileChange}
                disabled={isUploadDisabled}
                />
                <label
                htmlFor="pdfUpload"
                className={`${styles.customFileInput} ${
                    isUploadDisabled ? styles.disabled : ""
                }`}
                >
                {pdfFileName || "No file chosen"}
                </label>
            </div>
            </div>

            {/* Progress Bar */}
            {uploadProgress > 0 && (
            <div className={styles.progressBar}>
                <div
                className={styles.progress}
                style={{ width: `${uploadProgress}%` }}
                ></div>
            </div>
            )}

            {/* Buttons */}
            <div className={styles.buttonContainer}>
            <button
                className={`${styles.uploadButton} ${
                isUploadDisabled ? styles.disabled : ""
                }`}
                onClick={handleUpload}
                disabled={isUploadDisabled}
            >
                Upload PDF
            </button>

            <button
                className={`${styles.uploadButton} ${
                isFetchDisabled ? styles.disabled : ""
                }`}
                onClick={handleFetchGrade}
                disabled={isFetchDisabled}
            >
                Fetch Grade
            </button>
            </div>

            {/* Display the message */}
            {/* {message && <p className={styles.message}>{message}</p>} */}

            {grade && issues && (
            <div className={styles.gradeBox}>
                <h3>Grade Report:</h3>
                <p>
                <strong>Overall Grade:</strong>{" "}
                <span className={`${styles.grade} ${styles[grade.overall_grade]}`}>
                    {grade.overall_grade}
                </span>
                </p>
                <h3>Found Issues:</h3>
                {Array.isArray(issues) ? (
                <ul>
                    {issues.map((issue, index) => (
                    <li key={index}>{issue}.</li>
                    ))}
                </ul>
                ) : (
                <p>{issues}</p>
                )}
            </div>
            )}
        </div>
        </div>
    ) : (
        <main
        className={`${styles.mainSection} ${!pdfData ? styles.centeredContent : ""}`}
        >
        <h1 className={styles.title}>Upload and View PDF ✅</h1>

        <div className={styles.fileInputs}>
            <label htmlFor="pdfUpload" className={styles.label}>
            PDF File (Terms and Conditions):
            </label>
            <input
            type="file"
            id="pdfUpload"
            accept=".pdf"
            className={styles.fileInput}
            onChange={handleFileChange}
            />
            <span className={styles.fileName}>{pdfFileName}</span>
        </div>

        {/* Progress Bar */}
        {uploadProgress > 0 && (
            <div className={styles.progressBar}>
            <div
                className={styles.progress}
                style={{ width: `${uploadProgress}%` }}
            ></div>
            </div>
        )}
        {/* Display the message */}
        {message && <p className={styles.message}>{message}</p>}
        </main>
    )}
    </div>

  );
}
