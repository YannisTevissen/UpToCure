<?php
// Set headers to allow CORS and specify content type
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// Path to reports directory
$reportsDir = './reports';

// Initialize result array
$files = [];

// Check if directory exists
if (is_dir($reportsDir)) {
    // Get all files
    $allFiles = scandir($reportsDir);
    
    // Filter out dots and non-markdown files
    foreach ($allFiles as $file) {
        if ($file != '.' && $file != '..' && pathinfo($file, PATHINFO_EXTENSION) === 'md') {
            $files[] = $file;
        }
    }
}

// Return JSON-encoded array
echo json_encode($files);
?> 