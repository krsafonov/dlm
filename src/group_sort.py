#!/usr/bin/env python3
"""
Group sorting utility that:
1. Analyzes files in batches to identify groups for organization
2. Uses AI to suggest folder structures and file groupings
3. Saves results to .dlm directory for processing
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime


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


def run_gemini_group_analysis(
    directory: str, files: List[str], batch_size: int = 100
) -> Dict:
    """
    Run Gemini CLI to analyze files and identify groups for organization.
    
    Args:
        directory: Path to the directory to analyze
        files: List of file paths to analyze
        batch_size: Number of files to process in each batch
        
    Returns:
        Dictionary with group analysis results
    """
    all_results = []
    
    # Load prompt template
    try:
        prompt_template = load_prompt_template("group_analysis")
    except FileNotFoundError as e:
        return {"error": f"Prompt template not found: {e}"}
    
    # Process files in batches
    for i in range(0, len(files), batch_size):
        batch_files = files[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(files) + batch_size - 1) // batch_size
        
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch_files)} files)")
        
        # Create a list of just filenames for the prompt
        filenames = [Path(f).name for f in batch_files]
        files_list = "\n".join([f"- {name}" for name in filenames])
        
        # Format the prompt template
        prompt = prompt_template.format(
            directory=directory,
            files_list=files_list
        )
        
        try:
            # Run Gemini CLI command
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
            
            if "groups" in batch_result:
                all_results.extend(batch_result["groups"])
            else:
                print("Warning: No 'groups' key found in batch result")
                
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
    
    return {"groups": all_results}


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


def save_group_analysis(directory: str, groups: List[Dict]) -> None:
    """
    Save group analysis results to .dlm directory.
    
    Args:
        directory: Base directory
        groups: List of group analysis results
    """
    dlm_path = Path(directory) / ".dlm"
    dlm_path.mkdir(exist_ok=True)
    
    # Save groups to JSON file
    groups_file = dlm_path / "groups.json"
    with open(groups_file, 'w') as f:
        json.dump(groups, f, indent=2)
    
    print(f"📝 Saved {len(groups)} groups to {groups_file}")
    
    # Create summary files for easy viewing
    summary_file = dlm_path / "groups_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("GROUP ANALYSIS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        for group in groups:
            f.write(f"Group: {group['group_name']}\n")
            f.write(f"Description: {group['description']}\n")
            f.write(f"Files: {len(group['files'])} files\n")
            f.write(f"Size: {group['size_mb']} MB\n")
            f.write(f"Confidence: {group['confidence']}\n")
            f.write(f"Target folder: {group.get('suggested_folder', 'keep in place')}\n")
            if group.get('suggested_folder'):
                f.write(f"Folder: {group['suggested_folder']}\n")
            f.write("-" * 30 + "\n\n")
    
    print(f"📊 Created summary at {summary_file}")


def group_analysis(directory: str, batch_size: int = 100) -> Dict:
    """
    Complete group analysis of a directory using Gemini CLI.
    
    Args:
        directory: Path to the directory to analyze
        batch_size: Number of files to process in each batch
        
    Returns:
        Dictionary with complete analysis results
    """
    print(f"🔍 Analyzing files for grouping in: {directory}")
    
    # Step 1: Get files
    print("1. Retrieving files...")
    files = get_first_level_files(directory)
    print(f"   Found {len(files)} files")
    
    if not files:
        print("   No files found to analyze")
        return {"groups": []}
    
    # Step 2: Run Gemini analysis
    print("2. Running Gemini CLI group analysis...")
    results = run_gemini_group_analysis(directory, files, batch_size)
    
    if results.get("error"):
        print(f"❌ Error: {results['error']}")
        return results
    
    # Step 3: Save results
    print("3. Saving results...")
    groups = results.get("groups", [])
    save_group_analysis(directory, groups)
    
    return {
        "directory": directory,
        "files": files,
        "groups": groups,
        "summary": {"total_files": len(files), "total_groups": len(groups)}
    }


