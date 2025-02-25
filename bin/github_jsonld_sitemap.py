#!/usr/bin/env python3
"""
GitHub JSON-LD Sitemap Generator

This script generates a sitemap.xml file for JSON-LD files found in a specified GitHub repository directory.
It uses the GitHub API to scan the repository and creates a sitemap containing the raw URLs of all JSON-LD files.

Usage:
    ./github_jsonld_sitemap.py <repo_url> <directory> [--token GITHUB_TOKEN] [--output OUTPUT_FILE]

Arguments:
    repo_url        The GitHub repository URL (e.g., https://github.com/owner/repo)
    directory       The directory path within the repository to scan for JSON-LD files
    --token         GitHub personal access token (optional, can also be set via GITHUB_TOKEN env variable)
    --output        Output file path for the sitemap (default: sitemap.xml)

Example:
    # Basic usage
    ./github_jsonld_sitemap.py https://github.com/owner/repo data/jsonld

    # With custom output file and GitHub token
    ./github_jsonld_sitemap.py https://github.com/owner/repo data/jsonld --output custom_sitemap.xml --token YOUR_TOKEN

    # Using environment variable for GitHub token
    export GITHUB_TOKEN=your_token
    ./github_jsonld_sitemap.py https://github.com/owner/repo data/jsonld

Note:
    - The script will look for files with .jsonld or .json extensions
    - A GitHub token may be required for private repositories or to avoid rate limiting
    - The generated sitemap follows the standard sitemap.org schema
"""

import argparse
import os
from datetime import datetime
from typing import List
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from github import Github
from github.Repository import Repository
from github.ContentFile import ContentFile

def parse_github_url(url: str) -> tuple:
    """Parse GitHub URL to extract owner and repo name."""
    parts = url.strip('/').split('/')
    if 'github.com' in parts:
        idx = parts.index('github.com')
        if len(parts) > idx + 2:
            return parts[idx + 1], parts[idx + 2]
    raise ValueError("Invalid GitHub URL format")

def get_jsonld_files(repo: Repository, directory: str) -> List[ContentFile]:
    """Get all JSON-LD files from specified directory."""
    try:
        contents = repo.get_contents(directory)
        return [
            content for content in contents
            if content.type == "file" and
            (content.name.endswith('.jsonld') or content.name.endswith('.json'))
        ]
    except Exception as e:
        print(f"Error accessing directory {directory}: {str(e)}")
        return []

def generate_sitemap(files: List[ContentFile], output_file: str = "sitemap.xml"):
    """Generate sitemap.xml file from list of GitHub content files."""
    # Create the root element
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Add each file to the sitemap
    for file in files:
        url = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = file.download_url

        lastmod = ET.SubElement(url, "lastmod")
        lastmod.text = datetime.now().strftime("%Y-%m-%d")

    # Create the XML tree and write to file
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

def main():
    parser = argparse.ArgumentParser(description="Generate sitemap.xml for JSON-LD files in a GitHub repository")
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument("directory", help="Directory path within the repository")
    parser.add_argument("--token", help="GitHub personal access token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--output", help="Output file path", default="sitemap.xml")

    args = parser.parse_args()

    try:
        # Initialize GitHub API
        g = Github(args.token) if args.token else Github()

        # Parse repository information
        owner, repo_name = parse_github_url(args.repo_url)
        repo = g.get_repo(f"{owner}/{repo_name}")

        # Get JSON-LD files
        files = get_jsonld_files(repo, args.directory)

        if not files:
            print(f"No JSON-LD files found in {args.directory}")
            return

        # Generate sitemap
        generate_sitemap(files, args.output)
        print(f"Sitemap generated successfully at {args.output}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
