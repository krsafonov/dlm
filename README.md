# File Organization Utilities

This project provides intelligent file organization tools that use AI (Gemini CLI) to analyze and categorize files, then organize them into folders with full revert capability.

## Features

- **AI-Powered Analysis**: Uses Gemini CLI to intelligently identify important files and trash files
- **Batch Processing**: Handles large directories efficiently with configurable batch sizes
- **File Organization**: Moves files into organized folders based on analysis results
- **Full Revert Capability**: Complete undo functionality with detailed move logs
- **Flexible Prompts**: Customizable AI prompts stored in separate template files

## Files

- `dlm.py` - Main CLI entry point for all operations
- `src/initial_sort.py` - Analysis library that uses Gemini CLI to categorize files
- `src/file_organizer.py` - File organization library with core functions
- `prompts/important_files.txt` - AI prompt template for identifying important files
- `prompts/trash_files.txt` - AI prompt template for identifying trash files
- `example_organizer.py` - Example usage of the organizer functions

## Installation

1. Install Gemini CLI: `pip install google-generativeai`
2. Set up your Gemini API key
3. Ensure Python 3.7+ is installed

## Usage

### CLI Commands

DLM provides a simple CLI with 5 main commands:

#### 1. Find Important Files
```bash
python dlm.py find-important ~/Downloads
```
Saves list of important files to `.dlm/important_files.txt`
- If the file already exists, asks whether to run analysis again

#### 2. Find Trash Files
```bash
python dlm.py find-trash ~/Downloads
```
Saves list of trash files to `.dlm/trash_files.txt`
- If the file already exists, asks whether to run analysis again

#### 3. Find All Files
```bash
python dlm.py find-all ~/Downloads
```
Runs both find-important and find-trash

#### 4. Initial Organization
```bash
python dlm.py initial-organize ~/Downloads
```
Moves files according to lists created by find commands (basic organization)

#### 5. Revert Organization
```bash
python dlm.py revert ~/Downloads
```
Reverts all file moves using the move log

#### 6. Find Groups
```bash
python dlm.py find-groups ~/Downloads
```
Analyzes files and identifies groups for organization, saves to `.dlm/groups.json`

#### 7. Organize Groups
```bash
python dlm.py organize-groups ~/Downloads
```
Moves files according to group analysis results

#### 8. Revert Groups
```bash
python dlm.py revert-groups ~/Downloads
```
Reverts group organization and clears the move log

#### 9. Revert All
```bash
python dlm.py revert-all ~/Downloads
```
Reverts any organization (initial or groups) - automatically detects which logs exist

### Programmatic Usage

You can also use the library functions directly in Python:

```python
from src.file_organizer import create_folders, move_files_to_dir, revert_moves

# Create folders
folders = create_folders("~/Downloads", ["important", "trash"])

# Move files to directories
move_files_to_dir("~/Downloads", ["file1.pdf", "file2.doc"], "important", "moves.json")
move_files_to_dir("~/Downloads", ["temp.tmp", "old.log"], "trash", "moves.json")

# Revert all changes
revert_moves("moves.json")
```

## API Reference

### dlm.py (CLI)
- `command` - One of: find-important, find-trash, find-all, initial-organize, revert, find-groups, organize-groups, revert-groups, revert-all
- `directory` - Directory to process
- `--batch-size, -b` - Files per batch (default: 100)

### file_organizer.py (Library Functions)

#### `create_folders(base_dir, folder_names, log_file=None)`
- `base_dir` - Base directory where folders will be created
- `folder_names` - List of folder names to create
- `log_file` - Optional log file for tracking folder creation
- Returns: Dictionary mapping folder names to folder paths

#### `move_files_to_dir(base_dir, files, target_dir, log_file=None)`
- `base_dir` - Base directory containing the files
- `files` - List of filenames to move
- `target_dir` - Target directory name (relative to base_dir)
- `log_file` - Optional log file for tracking moves
- Returns: Dictionary with move results

#### `revert_moves(log_file)`
- `log_file` - Path to the move log file
- Returns: Dictionary with revert results (includes `reverted`, `folders_removed`, `errors`, `not_found`)

## Example Workflow

```bash
# 1. Find important files
python dlm.py find-important ~/Downloads

# 2. Find trash files  
python dlm.py find-trash ~/Downloads

# 3. Initial organization of files into folders
python dlm.py initial-organize ~/Downloads

# 4. If you want to revert everything back
python dlm.py revert ~/Downloads
```

Or run everything at once:
```bash
# Find all files and do initial organization in one go
python dlm.py find-all ~/Downloads
python dlm.py initial-organize ~/Downloads
```

## File Organization Structure

When doing initial organization, the utility creates the following folder structure:

- `important/` - Files marked as truly important
- `trash/` - Files that are clearly safe to delete
- `[group_folders]/` - Folders created based on group analysis
- `.dlm/` - Hidden directory containing:
  - `important_files.txt` - List of important files
  - `trash_files.txt` - List of trash files
  - `groups.json` - Group analysis results
  - `move_log.json` - Log of all file moves for reversion
  - `group_move_log.json` - Log of group organization moves

## Move Log Format

The move log is a JSON file that tracks all file movements and folder creation:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "base_directory": "/path/to/directory",
  "total_moves": 5,
  "moves": [
    {
      "timestamp": "2024-01-01T12:00:00",
      "source": "/path/to/original/file.pdf",
      "target": "/path/to/organized/important/file.pdf",
      "filename": "file.pdf"
    }
  ],
  "folders_created": [
    {
      "timestamp": "2024-01-01T12:00:00",
      "action": "create_folder",
      "folder_name": "important",
      "folder_path": "/path/to/directory/important"
    }
  ]
}
```

## Safety Features

- **Dry Run Mode**: Preview changes before applying them
- **Move Logging**: Complete audit trail of all file movements and folder creation
- **Conflict Resolution**: Handles duplicate filenames automatically
- **Error Handling**: Graceful handling of missing files and permission issues
- **Full Revert**: Complete undo capability for all operations (files and folders)

## Customization

### Modifying AI Prompts

Edit the prompt templates in the `prompts/` folder to customize how the AI categorizes files:

- `prompts/important_files.txt` - For identifying important files
- `prompts/trash_files.txt` - For identifying trash files

### Batch Size Tuning

Adjust the `--batch-size` parameter based on your system and Gemini API limits:
- Smaller batches (10-50): More reliable, slower
- Larger batches (100-500): Faster, may hit API limits

## Troubleshooting

### Common Issues

1. **Gemini CLI not found**: Install with `pip install google-generativeai`
2. **API limits**: Reduce batch size with `--batch-size 10`
3. **Permission errors**: Ensure write access to the target directory
4. **Missing files**: Check that source files exist before organizing

### Getting Help

Run the CLI with `--help` to see detailed usage information:
```bash
python dlm.py --help
```
