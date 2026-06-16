#!/bin/bash
# Configuración inicial de Firebase para Notaría 4 Digital Core
# Este script documenta los pasos y configuraciones necesarias.

echo "Iniciando configuración base de Firebase..."

# 1. Instalar dependencias globales (asumiendo Node.js instalado)
# npm install -g firebase-tools

# 2. Login a Firebase
# firebase login

# 3. Inicializar el proyecto (Ejecutar interactivamente)
# firebase init hosting,firestore,storage,remoteconfig

echo "Generando firebase.json..."
cat << 'JSON_EOF' > firebase.json
{
  "hosting": {
    "public": "build",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  },
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "storage": {
    "rules": "storage.rules"
  },
  "remoteconfig": {
    "template": "remoteconfig.template.json"
  }
}
JSON_EOF

echo "Generando reglas de Firestore (Seguridad)..."
cat << 'RULES_EOF' > firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Regla global: Solo usuarios autenticados de la notaría
    match /{document=**} {
      allow read, write: if request.auth != null;
    }

    // Regla específica: Bloqueo de expedientes timbrados
    match /expedientes/{expedienteId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth != null && (resource.data.status != 'Timbrado' || request.auth.token.admin == true);
      allow delete: if request.auth != null && request.auth.token.admin == true;
    }
  }
}
RULES_EOF

echo "Generando template de Remote Config (Tasa ISAI)..."
cat << 'RC_EOF' > remoteconfig.template.json
{
  "parameters": {
    "tasa_isai_manzanillo": {
      "defaultValue": {
        "value": "0.03"
      },
      "valueType": "NUMBER",
      "description": "Tasa del Impuesto Sobre Adquisición de Inmuebles para Manzanillo, Colima."
    }
  }
}
RC_EOF

echo "Generando reglas de Storage..."
cat << 'STOR_EOF' > storage.rules
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      // Solo autenticados pueden subir o leer PDFs/XMLs
      allow read, write: if request.auth != null;
    }
  }
}
STOR_EOF

echo "Configuración generada con éxito."
echo "Para desplegar las reglas, ejecuta: firebase deploy --only firestore:rules,storage,remoteconfig"
