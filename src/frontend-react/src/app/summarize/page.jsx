'use client';

import React, { useState, useEffect } from 'react';
import styles from './styles.module.css';

export default function FileUploadPage() {
    const [isClient, setIsClient] = useState(false);
    const [files, setFiles] = useState([]);
    const [uploadProgress, setUploadProgress] = useState({});

    useEffect(() => {
        setIsClient(true);
    }, []);

    const handleFileDrop = (event) => {
        event.preventDefault();
        const newFiles = Array.from(event.dataTransfer.files);
        uploadFiles(newFiles);
    };

    const handleFileSelect = (event) => {
        const newFiles = Array.from(event.target.files);
        uploadFiles(newFiles);
    };

    const uploadFiles = (newFiles) => {
        const newFileList = [...files, ...newFiles];
        setFiles(newFileList);

        newFiles.forEach((file) => {
            const uploadId = file.name;
            setUploadProgress((prev) => ({ ...prev, [uploadId]: 0 }));

            // Simulate file upload
            const simulateUpload = setInterval(() => {
                setUploadProgress((prev) => {
                    const progress = Math.min(prev[uploadId] + 10, 100);
                    if (progress === 100) clearInterval(simulateUpload);
                    return { ...prev, [uploadId]: progress };
                });
            }, 300);
        });
    };

    if (!isClient) {
        return null;
    }

    return (
        <div className={styles.container}>
            <main className={styles.mainSection}>
                <h1 className={styles.title}>Upload</h1>
                <div className={styles.uploadBox} onDrop={handleFileDrop} onDragOver={(e) => e.preventDefault()}>
                    <div className={styles.uploadContent}>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={2}
                            stroke="currentColor"
                            className={styles.uploadIcon}
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M12 16v-8m0 8l4-4m-4 4l-4-4m-6 6a9 9 0 0118 0H6z"
                            />
                        </svg>
                        <p>Drag & drop files or <label htmlFor="fileInput" className={styles.browseLink}>Browse</label></p>
                        <p className={styles.supportedFormats}>Supported formats: JPEG, PNG, GIF, MP4, PDF, PSD, AI, Word, PPT</p>
                        <input
                            id="fileInput"
                            type="file"
                            multiple
                            className={styles.hiddenInput}
                            onChange={handleFileSelect}
                        />
                    </div>
                </div>
                <button className={styles.uploadButton}>UPLOAD FILES</button>
            </main>

            {files.length > 0 && (
                <section className={styles.fileListSection}>
                    <h3 className={styles.fileListTitle}>Uploading - {files.length} file(s)</h3>
                    <div className={styles.fileList}>
                        {files.map((file, index) => (
                            <div key={index} className={styles.fileItem}>
                                <span>{file.name}</span>
                                <div className={styles.progressBar}>
                                    <div
                                        className={styles.progress}
                                        style={{ width: `${uploadProgress[file.name] || 0}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}