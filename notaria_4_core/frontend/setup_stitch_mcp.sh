#!/bin/bash

# Setup script for integrating Google Stitch MCP into Claude Code
# Usage: ./setup_stitch_mcp.sh <YOUR_STITCH_API_KEY>

if [ -z "$1" ]; then
  echo "Error: Stitch API Key is required."
  echo "Usage: $0 <YOUR_STITCH_API_KEY>"
  echo "You can get your API key from https://stitch.withgoogle.com/"
  exit 1
fi

API_KEY=$1

echo "Configuring Stitch MCP server for Claude Code..."

# Assuming claude is installed and available in PATH
# Execute the MCP add command
claude mcp add stitch --transport http https://stitch.googleapis.com/mcp --header "X-Goog-Api-Key: $API_KEY" -s user

if [ $? -eq 0 ]; then
  echo "Successfully added Stitch MCP server to Claude Code configuration."
  echo "You can now use Claude Code to generate UI based on your Stitch projects!"
  echo "To verify, check your claude.json configuration file."
else
  echo "Failed to add Stitch MCP server. Please ensure 'claude' CLI is installed and updated."
fi
