#!/usr/bin/env python3
"""
File organization utility that:
1. Retrieves first-level file extensions from a directory
2. Uses Gemini CLI to identify important files
3. Identifies potential trash files
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List


def run_gemini_batch_analysis(
    directory: str,
    files: List[str],
    prompt_template: str,
    flag_name: str,
    batch_size: int = 100,
) -> Dict:
    """
    Generic function to run Gemini CLI analysis on files in batches.

    Args:
        directory: Path to the directory to analyze
        files: List of file paths to analyze
        prompt_template: Template string for the prompt (from prompts folder)
        flag_name: Name of the flag to extract (e.g., 'important', 'trash')
        batch_size: Number of files to process in each batch

    Returns:
        Dictionary with analysis results
    """
    all_results = []

    # Process files in batches
    for i in range(0, len(files), batch_size):
        batch_files = files[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(files) + batch_size - 1) // batch_size
        print(
            f"Processing batch {batch_num}/{total_batches} ({len(batch_files)} files)"
        )

        # Create a list of just filenames for the prompt
        filenames = [Path(f).name for f in batch_files]
        files_list = "\n".join([f"- {name}" for name in filenames])

        # Format the prompt template
        prompt = prompt_template.format(directory=directory, files_list=files_list)

        try:
            # Run Gemini CLI command with the correct syntax
            cmd = ["gemini", "--prompt", prompt, "--include-directories", directory]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse the JSON response
            response_text = result.stdout.strip()

            # Find the JSON part in the response
            json_start = response_text.find("{")
            if json_start == -1:
                raise ValueError("No JSON found in Gemini response")

            # Find the end of the JSON object by balancing braces
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(response_text[json_start:], json_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            json_str = response_text[json_start:json_end]
            batch_result = json.loads(json_str)

            if "file_analysis" in batch_result:
                all_results.extend(batch_result["file_analysis"])
            else:
                print("Warning: No 'file_analysis' key found in batch result")

        except subprocess.CalledProcessError as e:
            print(f"Error running Gemini CLI: {e}")
            print(f"Command: {' '.join(cmd)}")
            print(f"Error output: {e.stderr}")
            return {"error": f"Gemini CLI failed: {e.stderr}"}
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response as JSON: {e}")
            print(f"Response: {response_text}")
            return {"error": f"Failed to parse JSON: {e}"}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {"error": f"Unexpected error: {e}"}

    return {"file_analysis": all_results}


def load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the prompts folder.

    Args:
        template_name: Name of the template file (without .txt extension)

    Returns:
        Template string content
    """
    template_path = Path(__file__).parent.parent / "prompts" / f"{template_name}.txt"

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    return template_path.read_text()


def get_first_level_files(directory: str) -> List[str]:
    """
    Retrieve all first-level files from a directory.

    Args:
        directory: Path to the directory to analyze

    Returns:
        List of file paths (first level only, no directories)
    """
    files = []
    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory {directory} does not exist")

    if not directory_path.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")

    # Get all files in the directory (first level only)
    for item in directory_path.iterdir():
        if item.is_file():
            files.append(str(item))

    return sorted(files)


def run_gemini_important_analysis(
    directory: str, files: List[str], batch_size: int = 100
) -> Dict:
    """
    Run Gemini CLI to analyze individual files and identify important ones.

    Args:
        directory: Path to the directory to analyze
        files: List of file paths to analyze
        batch_size: Number of files to process in each batch (default: 100)

    Returns:
        Dictionary with Gemini's analysis results
    """
    try:
        prompt_template = load_prompt_template("important_files")
        return run_gemini_batch_analysis(
            directory, files, prompt_template, "important", batch_size
        )
    except FileNotFoundError as e:
        return {"error": f"Prompt template not found: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


def run_gemini_trash_analysis(
    directory: str, files: List[str], batch_size: int = 100
) -> Dict:
    """
    Run Gemini CLI to identify clear trash files that are safe to delete.

    Args:
        directory: Path to the directory to analyze
        files: List of file paths to analyze
        batch_size: Number of files to process in each batch (default: 100)

    Returns:
        Dictionary with Gemini's trash analysis results
    """
    try:
        prompt_template = load_prompt_template("trash_files")
        return run_gemini_batch_analysis(
            directory, files, prompt_template, "trash", batch_size
        )
    except FileNotFoundError as e:
        return {"error": f"Prompt template not found: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


def initial_analysis(
    directory: str, batch_size: int = 100, mode: str = "important"
) -> Dict:
    """
    Initial analysis of a directory using Gemini CLI.

    Args:
        directory: Path to the directory to analyze
        batch_size: Number of files to process in each batch
        mode: Analysis mode - "important" or "trash"

    Returns:
        Dictionary with complete analysis results
    """
    print(f"Analyzing directory: {directory}")

    # Step 1: Get files
    print("1. Retrieving files...")
    files = get_first_level_files(directory)
    print(f"   Found {len(files)} files")

    # Step 2: Run Gemini analysis
    if mode == "important":
        print("2. Running Gemini CLI analysis for important files...")
        gemini_results = run_gemini_important_analysis(directory, files, batch_size)
    elif mode == "trash":
        print("2. Running Gemini CLI analysis for trash files...")
        gemini_results = run_gemini_trash_analysis(directory, files, batch_size)
    else:
        raise ValueError("Mode must be 'important' or 'trash'")

    return {
        "directory": directory,
        "files": files,
        "gemini_analysis": gemini_results,
        "summary": {"total_files": len(files)},
    }


