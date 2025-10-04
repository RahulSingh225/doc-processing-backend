from app.operations.base import OperationBase
from typing import Dict, Any
from pyresparser import ResumeParser
from transformers import pipeline
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os
import json

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('pdf', 'docx', 'json')  # Input PDF/DOCX, output JSON

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}_insights.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, os.path.basename(input_key))
            output_path = os.path.join(tmpdir, 'insights.json')

            download_from_s3(input_key, input_path)
            try:
                # Parse resume sections using pyresparser
                parser = ResumeParser(input_path)
                data = parser.get_extracted_data()

                # Extracted sections (standardized)
                parsed_sections = {
                    "personal_details": {
                        "name": data.get('name'),
                        "email": data.get('email'),
                        "phone": data.get('mobile_number'),
                        "location": data.get('designation')  # Approx
                    },
                    "education": data.get('degree', []),
                    "experience": data.get('experience', []),
                    "skills": data.get('skills', []),
                    "hobbies": data.get('hobbies', []),  # If extracted; else custom logic
                    "other": {
                        "companies": data.get('company_names', []),
                        "projects": data.get('project', [])
                    }
                }

                # AI Insights: Use transformers for analysis
                # Example: Zero-shot classification for skills relevance (e.g., to a job role)
                # And text generation for suggestions
                job_role = inputs['options'].get('job_role', 'software engineer')  # From request options

                # Load pipelines (lightweight models for efficiency)
                classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
                generator = pipeline("text-generation", model="distilgpt2", max_new_tokens=50)

                # Insight 1: Skills matching to job
                skills_text = ", ".join(parsed_sections['skills'])
                skill_insights = classifier(skills_text, candidate_labels=[f"relevant to {job_role}", "irrelevant", "needs improvement"])
                parsed_sections['insights'] = {
                    "skills_match": skill_insights['labels'][0],
                    "score": skill_insights['scores'][0]
                }

                # Insight 2: Suggest improvements for experience bullets
                experience_text = " ".join(parsed_sections['experience'])
                prompt = f"Rephrase this experience for better impact in a {job_role} resume: {experience_text[:500]}"  # Truncate for efficiency
                suggestions = generator(prompt)[0]['generated_text']
                parsed_sections['insights']['experience_suggestions'] = suggestions

                # Add more insights (e.g., education gaps, keyword optimization via freq analysis)

                # Save as JSON
                with open(output_path, 'w') as f:
                    json.dump(parsed_sections, f, indent=4)
                upload_to_s3(output_path, output_key)

                metadata = {'sections_extracted': len(parsed_sections)}

            except Exception as e:
                raise ValueError(f"Resume processing failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}from app.operations.base import OperationBase
from typing import Dict, Any
from pyresparser import ResumeParser
from transformers import pipeline
from app.utils import download_from_s3, upload_to_s3
import tempfile
import os
import json

class Operation(OperationBase):
    @property
    def supported_formats(self) -> tuple:
        return ('pdf', 'docx', 'json')  # Input PDF/DOCX, output JSON

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        input_key = inputs['file_keys'][0]
        output_key = f"processed/{inputs['job_id']}_insights.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, os.path.basename(input_key))
            output_path = os.path.join(tmpdir, 'insights.json')

            download_from_s3(input_key, input_path)
            try:
                # Parse resume sections using pyresparser
                parser = ResumeParser(input_path)
                data = parser.get_extracted_data()

                # Extracted sections (standardized)
                parsed_sections = {
                    "personal_details": {
                        "name": data.get('name'),
                        "email": data.get('email'),
                        "phone": data.get('mobile_number'),
                        "location": data.get('designation')  # Approx
                    },
                    "education": data.get('degree', []),
                    "experience": data.get('experience', []),
                    "skills": data.get('skills', []),
                    "hobbies": data.get('hobbies', []),  # If extracted; else custom logic
                    "other": {
                        "companies": data.get('company_names', []),
                        "projects": data.get('project', [])
                    }
                }

                # AI Insights: Use transformers for analysis
                # Example: Zero-shot classification for skills relevance (e.g., to a job role)
                # And text generation for suggestions
                job_role = inputs['options'].get('job_role', 'software engineer')  # From request options

                # Load pipelines (lightweight models for efficiency)
                classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
                generator = pipeline("text-generation", model="distilgpt2", max_new_tokens=50)

                # Insight 1: Skills matching to job
                skills_text = ", ".join(parsed_sections['skills'])
                skill_insights = classifier(skills_text, candidate_labels=[f"relevant to {job_role}", "irrelevant", "needs improvement"])
                parsed_sections['insights'] = {
                    "skills_match": skill_insights['labels'][0],
                    "score": skill_insights['scores'][0]
                }

                # Insight 2: Suggest improvements for experience bullets
                experience_text = " ".join(parsed_sections['experience'])
                prompt = f"Rephrase this experience for better impact in a {job_role} resume: {experience_text[:500]}"  # Truncate for efficiency
                suggestions = generator(prompt)[0]['generated_text']
                parsed_sections['insights']['experience_suggestions'] = suggestions

                # Add more insights (e.g., education gaps, keyword optimization via freq analysis)

                # Save as JSON
                with open(output_path, 'w') as f:
                    json.dump(parsed_sections, f, indent=4)
                upload_to_s3(output_path, output_key)

                metadata = {'sections_extracted': len(parsed_sections)}

            except Exception as e:
                raise ValueError(f"Resume processing failed: {str(e)}")

        return {'output_key': output_key, 'metadata': metadata}