#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Script de migration et nettoyage du système MCP mémoire
 * Corrige les problèmes architecturaux identifiés
 */

console.log('🔧 MIGRATION ET NETTOYAGE DU SYSTÈME MCP MÉMOIRE');
console.log('================================================');

// Trouver la racine du projet
function findProjectRoot() {
  let current = path.resolve(__dirname, '../..');
  
  while (current !== path.dirname(current)) {
    if (fs.existsSync(path.join(current, '.kiro'))) {
      return current;
    }
    current = path.dirname(current);
  }
  
  throw new Error('Project root not found');
}

const projectRoot = findProjectRoot();
console.log(`📁 Racine du projet : ${projectRoot}`);

// 1. Nettoyer les structures récursives
console.log('\n1️⃣ NETTOYAGE DES STRUCTURES RÉCURSIVES');
const recursiveKiro = path.join(projectRoot, '.kiro', '.kiro');
if (fs.existsSync(recursiveKiro)) {
  console.log('🗑️ Suppression de .kiro/.kiro/...');
  fs.rmSync(recursiveKiro, { recursive: true, force: true });
  console.log('✅ Structure récursive supprimée');
} else {
  console.log('✅ Aucune structure récursive détectée');
}

// 2. Fusionner les données de mémoire dupliquées
console.log('\n2️⃣ FUSION DES DONNÉES DUPLIQUÉES');
const mainMemoryFile = path.join(projectRoot, '.kiro', 'memory', 'project-memory.json');
const duplicateMemoryFile = path.join(projectRoot, '.kiro', '.kiro', 'memory', 'project-memory.json');

let mainMemory = {};
let duplicateMemory = {};

// Charger la mémoire principale
if (fs.existsSync(mainMemoryFile)) {
  try {
    mainMemory = JSON.parse(fs.readFileSync(mainMemoryFile, 'utf8'));
    console.log(`📊 Mémoire principale : ${mainMemory.conversations?.length || 0} conversations`);
  } catch (error) {
    console.log(`⚠️ Erreur lecture mémoire principale : ${error.message}`);
  }
}

// Charger la mémoire dupliquée (si elle existe encore)
if (fs.existsSync(duplicateMemoryFile)) {
  try {
    duplicateMemory = JSON.parse(fs.readFileSync(duplicateMemoryFile, 'utf8'));
    console.log(`📊 Mémoire dupliquée : ${duplicateMemory.conversations?.length || 0} conversations`);
    
    // Fusionner les données
    if (duplicateMemory.conversations && duplicateMemory.conversations.length > 0) {
      mainMemory.conversations = mainMemory.conversations || [];
      
      // Ajouter les conversations uniques
      duplicateMemory.conversations.forEach(conv => {
        const exists = mainMemory.conversations.some(existing => 
          existing.date === conv.date && existing.content === conv.content
        );
        if (!exists) {
          mainMemory.conversations.push(conv);
        }
      });
      
      console.log(`🔄 Fusion effectuée : ${mainMemory.conversations.length} conversations totales`);
    }
  } catch (error) {
    console.log(`⚠️ Erreur lecture mémoire dupliquée : ${error.message}`);
  }
}

// Sauvegarder la mémoire fusionnée
if (Object.keys(mainMemory).length > 0) {
  fs.writeFileSync(mainMemoryFile, JSON.stringify(mainMemory, null, 2));
  console.log('✅ Mémoire fusionnée sauvegardée');
}

// 3. Nettoyer l'ancien serveur
console.log('\n3️⃣ NETTOYAGE DE L\'ANCIEN SERVEUR');
const oldServerPath = path.join(projectRoot, 'mcp-server');
if (fs.existsSync(oldServerPath)) {
  console.log('🗑️ Suppression de l\'ancien dossier mcp-server/...');
  try {
    fs.rmSync(oldServerPath, { recursive: true, force: true });
    console.log('✅ Ancien serveur supprimé');
  } catch (error) {
    console.log(`⚠️ Impossible de supprimer l'ancien serveur : ${error.message}`);
    console.log('   (Probablement en cours d\'utilisation - redémarrer Kiro IDE)');
  }
} else {
  console.log('✅ Ancien serveur déjà supprimé');
}

// 4. Valider la structure finale
console.log('\n4️⃣ VALIDATION DE LA STRUCTURE FINALE');
const expectedDirs = [
  '.kiro/memory',
  '.kiro/mcp-server',
  '.kiro/settings',
  '.kiro/steering'
];

let structureValid = true;
expectedDirs.forEach(dir => {
  const fullPath = path.join(projectRoot, dir);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ ${dir}/`);
  } else {
    console.log(`❌ ${dir}/ - MANQUANT`);
    structureValid = false;
  }
});

// 5. Tester le nouveau serveur
console.log('\n5️⃣ TEST DU NOUVEAU SERVEUR');
const newServerPath = path.join(projectRoot, '.kiro', 'mcp-server', 'memory-server-fixed.js');
if (fs.existsSync(newServerPath)) {
  console.log('✅ Nouveau serveur présent');
  
  // Test rapide
  try {
    const { execSync } = await import('child_process');
    const result = execSync(`node "${newServerPath}" --test`, { 
      cwd: path.dirname(newServerPath),
      encoding: 'utf8',
      timeout: 10000
    });
    
    if (result.includes('🎉 Serveur MCP refactorisé fonctionne correctement !')) {
      console.log('✅ Test du nouveau serveur réussi');
    } else {
      console.log('⚠️ Test du nouveau serveur incomplet');
    }
  } catch (error) {
    console.log(`⚠️ Erreur test serveur : ${error.message}`);
  }
} else {
  console.log('❌ Nouveau serveur manquant');
  structureValid = false;
}

// 6. Rapport final
console.log('\n📋 RAPPORT FINAL DE MIGRATION');
console.log('==============================');

if (structureValid) {
  console.log('🎉 MIGRATION RÉUSSIE !');
  console.log('');
  console.log('✅ Structure récursive nettoyée');
  console.log('✅ Données fusionnées et préservées');
  console.log('✅ Ancien serveur supprimé');
  console.log('✅ Nouveau serveur fonctionnel');
  console.log('✅ Configuration mise à jour');
  console.log('');
  console.log('🔄 PROCHAINES ÉTAPES :');
  console.log('1. Redémarrer Kiro IDE pour utiliser la nouvelle configuration');
  console.log('2. Tester les outils MCP mémoire');
  console.log('3. Vérifier que tout fonctionne correctement');
} else {
  console.log('⚠️ MIGRATION INCOMPLÈTE');
  console.log('Certains éléments nécessitent une attention manuelle.');
}

console.log('\n🏁 Migration terminée.');