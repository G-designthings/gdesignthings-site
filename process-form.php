<?php

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $to = "ask@gdesignthings.com";
    $subject = "New form submission";

    // Sanitizacija podataka
    $name = filter_input(INPUT_POST, 'name', FILTER_SANITIZE_STRING);
    $email = filter_input(INPUT_POST, 'email', FILTER_VALIDATE_EMAIL);
    $cc = filter_input(INPUT_POST, 'cc', FILTER_SANITIZE_EMAIL);
    $bcc = filter_input(INPUT_POST, 'bcc', FILTER_SANITIZE_EMAIL);
    $message = filter_input(INPUT_POST, 'message', FILTER_SANITIZE_STRING);

    if (!$email) {
        // Ako e-mail nije validan, preusmeri na stranicu sa greškom
        header("Location: error.html?error=invalid_email");
        exit();
    }

    $headers = "From: " . $email . "\r\n";
    $headers .= "Reply-To: " . $email . "\r\n";
    if ($cc) {
        $headers .= "CC: " . $cc . "\r\n";
    }
    if ($bcc) {
        $headers .= "BCC: " . $bcc . "\r\n";
    }

    $emailBody = "Name: " . $name . "\r\n";
    $emailBody .= "Email: " . $email . "\r\n";
    $emailBody .= "Message: " . $message . "\r\n";

    // Inicijalizuj MIME za slanje sa prilozima
    $boundary = md5(time());
    $headers .= "MIME-Version: 1.0\r\n";
    $headers .= "Content-Type: multipart/mixed; boundary=\"$boundary\"\r\n\r\n";
    $emailBody = "--$boundary\r\n" . 
                 "Content-Type: text/plain; charset=UTF-8\r\n" . 
                 "Content-Transfer-Encoding: 7bit\r\n\r\n" .
                 $emailBody . "\r\n";

    // Obrada upload-ovanih datoteka
    if (isset($_FILES['file-upload']) && $_FILES['file-upload']['error'][0] !== UPLOAD_ERR_NO_FILE) {
        $total_files = count($_FILES['file-upload']['name']);
        
        for ($i = 0; $i < $total_files; $i++) {
            if ($_FILES['file-upload']['error'][$i] === UPLOAD_ERR_OK) {
                $tmpFilePath = $_FILES['file-upload']['tmp_name'][$i];
                $file_name = $_FILES['file-upload']['name'][$i];
                $file_size = $_FILES['file-upload']['size'][$i];
                $file_type = $_FILES['file-upload']['type'][$i];

                // Validacija tipa datoteke (npr. samo slike i PDF-ovi)
                $allowed_types = ['image/jpeg', 'image/png', 'application/pdf'];
                if (in_array($file_type, $allowed_types)) {
                    $path_parts = pathinfo($file_name);
                    $new_file_name = $path_parts['filename'] . "_" . time() . "." . $path_parts['extension'];
                    $new_file_path = "uploads/" . $new_file_name;

                    // Premesti datoteku u uploads direktorijum
                    move_uploaded_file($tmpFilePath, $new_file_path);

                    // Dodaj prilog e-mailu
                    $file = file_get_contents($new_file_path);
                    $file_content = chunk_split(base64_encode($file));
                    $emailBody .= "--$boundary\r\n";
                    $emailBody .= "Content-Type: $file_type; name=\"$new_file_name\"\r\n";
                    $emailBody .= "Content-Disposition: attachment; filename=\"$new_file_name\"\r\n";
                    $emailBody .= "Content-Transfer-Encoding: base64\r\n\r\n";
                    $emailBody .= $file_content . "\r\n";
                } else {
                    // U slučaju nevalidnog tipa datoteke, preusmeri na stranicu sa greškom
                    header("Location: error.html?error=invalid_file_type");
                    exit();
                }
            }
        }
        $emailBody .= "--$boundary--"; // Kraj MIME
    } else {
        $emailBody .= "--$boundary--"; // Kraj MIME
    }

    // Slanje e-maila
    if (mail($to, $subject, $emailBody, $headers)) {
        // Preusmeri na stranicu zahvalnosti
        header("Location: thank-you.html");
    } else {
        // U slučaju greške pri slanju, preusmeri na stranicu sa greškom
        header("Location: error.html?error=email_failed");
    }
    exit();
}

?>
