"use client";

import React, { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import DataService from "../../services/DataService";
import styles from "./styles.module.css";

import 'react-pdf/dist/esm/Page/TextLayer.css';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

export default function FileUploadPage() {
    const [pdfFile, setPdfFile] = useState(null);
    const [pdfData, setPdfData] = useState(null);
    const [numPages, setNumPages] = useState(null);
    const [pageNumber, setPageNumber] = useState(1);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [grade, setGrade] = useState(null);

    const handleFileChange = (event) => {
        const file = event.target.files[0];

        if (file && file.type === "application/pdf") {
            setPdfFile(file);

            const reader = new FileReader();
            reader.onload = (e) => setPdfData(e.target.result);
            reader.readAsArrayBuffer(file);
        } else {
            alert("Please upload a valid PDF file.");
        }
    };

    const onDocumentLoadSuccess = ({ numPages }) => {
        setNumPages(numPages);
        setPageNumber(1);
    };

    const handleUpload = async () => {
        if (!pdfFile) {
            alert("Please upload a PDF file first.");
            return;
        }

        try {
            setUploadProgress(10);
            const projectId = "473358048261";
            const locationId = "us-central1";
            const endpointId = "5609779793168957440";

            const response = await DataService.UploadFiles(pdfFile, null, projectId, locationId, endpointId);
            console.log("Upload response:", response);
            setUploadProgress(100);
            alert("PDF processed successfully. You can now fetch the grade.");
        } catch (error) {
            console.error("Error uploading PDF:", error);
            alert("Failed to process files.");
        }
    };

    const handleFetchGrade = async () => {
        try {
            const response = await DataService.GetGrade();
            console.log("Grade response:", response);
            setGrade(response);
        } catch (error) {
            console.error("Error fetching grade:", error);
            alert("Failed to fetch grade.");
        }
    };

    return (
        <div className={styles.container}>
            <main className={styles.mainSection}>
                <h1 className={styles.title}>Upload and View PDF</h1>

                <div className={styles.fileInputs}>
                    <label htmlFor="pdfUpload" className={styles.label}>PDF File (Terms and Conditions):</label>
                    <input
                        type="file"
                        id="pdfUpload"
                        accept=".pdf"
                        className={styles.fileInput}
                        onChange={handleFileChange}
                    />
                </div>

                {pdfData && (
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
                            >
                                Previous
                            </button>
                            <button
                                onClick={() => setPageNumber((prev) => Math.min(prev + 1, numPages))}
                                disabled={pageNumber >= numPages}
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}

                <button className={styles.uploadButton} onClick={handleUpload}>
                    Upload PDF
                </button>

                {uploadProgress > 0 && (
                    <div className={styles.progressBar}>
                        <div
                            className={styles.progress}
                            style={{ width: `${uploadProgress}%` }}
                        ></div>
                    </div>
                )}

                <button className={styles.uploadButton} onClick={handleFetchGrade}>
                    Fetch Grade
                </button>

                {grade && (
                    <div className={styles.gradeResult}>
                        <h2>Grade Report</h2>
                        <p><strong>Overall Grade:</strong> {grade.overall_grade}</p>
                        <p><strong>Overall Score:</strong> {grade.overall_score}</p>
                        <pre className={styles.preformatted}>
                            {JSON.stringify(grade.category_scores, null, 2)}
                        </pre>
                    </div>
                )}
            </main>
        </div>
    );
}