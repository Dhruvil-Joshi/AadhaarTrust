### Aadhaar Workflow:

#### Forged or not:
First of all, Load the image
Then create the noiseprint for the specific image
Now, Load the model and detect whether the model was forged or not

#### Which Area has been Forged:
Load the detection model
and map the image and detection model together on noiseprint
Give the percentage and store the image of that splicing

#### If valid, go for the QR detection:
Use a QR Code detection model, in which it can detect the QR codes
1. Direct DecodeDecode original image
2. Basic PreprocessingGrayscale → Contrast (CLAHE) → Sharpen → Threshold
3. QR Region ExtractionDetect contours → Crop QR area → Perspective correction
4. Multiple VariationsTry different thresholds, rotations, inverse, resize
If QR is not scanned yet, go for manual review

#### If the data is found from QR:
Start OCR on images and find the similarity between available data and Qr data and check the validity of the aadhaar


aadhaar-validation/
│
├── config/
│   ├── __init__.py
│   ├── settings.py              # Configuration parameters (thresholds, paths)
│   └── model_config.yaml        # Model-specific configurations
│
├── models/
│   ├── forgery/
│   │   ├── noiseprint_model.pth
│   │   └── detection_model.pth
│   └── qr/
│       └── qr_detection_model.pth
│
├── src/
│   ├── __init__.py
│   │
│   ├── forgery_detection/
│   │   ├── __init__.py
│   │   ├── noiseprint.py        # Noiseprint generation
│   │   ├── detector.py          # Forgery detection logic
│   │   └── localization.py      # Splicing area mapping
│   │
│   ├── qr_processing/
│   │   ├── __init__.py
│   │   ├── detector.py          # QR code detection
│   │   ├── decoder.py           # Progressive QR decoding (4 steps)
│   │   └── preprocessor.py      # Image enhancements (CLAHE, sharpen, etc.)
│   │
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── extractor.py         # OCR text extraction
│   │   └── validator.py         # Similarity check QR vs OCR
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── aadhaar_validator.py # Aadhaar number format check
│   │   └── data_matcher.py      # Cross-field validation logic
│   │
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py       # Image loading, preprocessing helpers
│       ├── logger.py            # Logging setup
│       └── report_generator.py  # PDF/HTML report generation
│
├── pipeline/
│   ├── __init__.py
│   └── main_pipeline.py         # Orchestrates entire workflow
│
├── data/
│   ├── input/                   # Input Aadhaar images
│   ├── output/
│   │   ├── reports/             # Generated validation reports
│   │   ├── splicing_maps/       # Forged area visualizations
│   │   └── processed_images/    # Intermediate processed images
│   └── manual_review/           # Failed cases for human review
│
├── logs/
│   ├── app.log                  # Application logs
│   └── errors.log               # Error logs
│
├── tests/
│   ├── __init__.py
│   ├── test_forgery.py
│   ├── test_qr.py
│   ├── test_ocr.py
│   └── test_pipeline.py
│
├── notebooks/
│   └── exploratory_analysis.ipynb  # For testing/debugging
│
├── requirements.txt             # Python dependencies
├── setup.py                     # Package installation
├── README.md                    # Documentation
└── main.py                      # Entry point for running pipeline