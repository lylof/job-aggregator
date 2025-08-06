#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 🏗️ ARCHITECTURE ROBUSTE - SÉPARATION DES RESPONSABILITÉS

/**
 * Gestionnaire de chemins robuste et portable
 */
class PathManager {
  static findProjectRoot(startPath = process.cwd()) {
    let current = path.resolve(startPath);
    
    // Remonte l'arborescence jusqu'à trouver .kiro/ ou package.json
    while (current !== path.dirname(current)) {
      if (fs.existsSync(path.join(current, '.kiro'))) {
        return current;
      }
      if (fs.existsSync(path.join(current, 'package.json'))) {
        // Vérifier si c'est le bon package.json (contient jinascraper)
        try {
          const pkg = JSON.parse(fs.readFileSync(path.join(current, 'package.json'), 'utf8'));
          if (pkg.name && pkg.name.includes('jinascraper')) {
            return current;
          }
        } catch {}
      }
      current = path.dirname(current);
    }
    
    throw new Error('Project root not found - no .kiro directory found in parent directories');
  }
  
  static getMemoryFile(projectRoot) {
    return path.join(projectRoot, '.kiro', 'memory', 'project-memory.json');
  }
  
  static getSteeringFile(projectRoot) {
    return path.join(projectRoot, '.kiro', 'steering', 'project-memory.md');
  }
}

/**
 * Gestionnaire de système de fichiers avec validation
 */
class FileSystemManager {
  static ensureDirectoryExists(dirPath) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }
  
  static validateAndRepairStructure(projectRoot) {
    const requiredDirs = [
      path.join(projectRoot, '.kiro'),
      path.join(projectRoot, '.kiro', 'memory'),
      path.join(projectRoot, '.kiro', 'steering')
    ];
    
    requiredDirs.forEach(dir => this.ensureDirectoryExists(dir));
    
    // Détecter et nettoyer les structures récursives
    const recursiveKiro = path.join(projectRoot, '.kiro', '.kiro');
    if (fs.existsSync(recursiveKiro)) {
      console.warn('🚨 Structure récursive détectée, nettoyage...');
      fs.rmSync(recursiveKiro, { recursive: true, force: true });
    }
  }
}

/**
 * Service de mémoire avec logique métier pure
 */
class MemoryService {
  constructor(projectRoot) {
    this.projectRoot = projectRoot;
    this.memoryFile = PathManager.getMemoryFile(projectRoot);
    this.steeringFile = PathManager.getSteeringFile(projectRoot);
    
    // Valider et réparer la structure au démarrage
    FileSystemManager.validateAndRepairStructure(projectRoot);
  }
  
  loadMemory() {
    try {
      if (!fs.existsSync(this.memoryFile)) {
        return this.getDefaultMemory();
      }
      const data = JSON.parse(fs.readFileSync(this.memoryFile, 'utf8'));
      return this.validateMemoryStructure(data);
    } catch (error) {
      console.warn(`Erreur lecture mémoire: ${error.message}, utilisation structure par défaut`);
      return this.getDefaultMemory();
    }
  }
  
  saveMemory(memory) {
    const validatedMemory = this.validateMemoryStructure(memory);
    fs.writeFileSync(this.memoryFile, JSON.stringify(validatedMemory, null, 2));
    this.updateSteeringMemory(validatedMemory);
  }
  
  getDefaultMemory() {
    return {
      conversations: [],
      technical_changes: [],
      patterns: {},
      performance_metrics: [],
      steering_context: {},
      intelligent_reminders: [],
      auto_detected_changes: []
    };
  }
  
  validateMemoryStructure(memory) {
    const defaultMemory = this.getDefaultMemory();
    const validated = { ...defaultMemory };
    
    // Fusionner les données existantes en préservant la structure
    Object.keys(defaultMemory).forEach(key => {
      if (memory[key] !== undefined) {
        validated[key] = memory[key];
      }
    });
    
    return validated;
  }
  
  updateSteeringMemory(memory) {
    const summary = this.generateMemorySummary(memory);
    fs.writeFileSync(this.steeringFile, summary);
  }
  
  generateMemorySummary(memory) {
    const now = new Date().toISOString();
    const conversations = memory.conversations || [];
    const technicalChanges = memory.technical_changes || [];
    const metrics = memory.performance_metrics || [];
    
    return `# 🧠 Mémoire Intelligente du Projet JinaScraper

**Dernière mise à jour**: ${now}

## 📊 Statistiques Globales
- **Conversations**: ${conversations.length}
- **Changements Techniques**: ${technicalChanges.length}
- **Changements Auto-détectés**: ${memory.auto_detected_changes?.length || 0}
- **Métriques Performance**: ${metrics.length}

## 🔧 Changements Techniques Récents
${technicalChanges.slice(-3).map(change => 
  `### ${change.type?.toUpperCase()} - ${new Date(change.timestamp).toLocaleDateString()}
- **Description**: ${change.description}
- **Fichiers**: ${change.files_modified?.join(', ') || 'N/A'}
- **Tags**: ${change.tags?.join(', ') || 'N/A'}`
).join('\n\n')}

## 🤖 Surveillance Automatique
- **Statut**: ❌ Inactive
- **Fichiers surveillés**: services/, core/, config/, .kiro/
- **Dernière analyse**: ${now}

`;
  }
}

// 🚀 SERVEUR MCP SIMPLIFIÉ
const memoryService = new MemoryService(PathManager.findProjectRoot());

const server = new Server({
  name: "intelligent-memory-fixed",
  version: "3.0.0",
}, {
  capabilities: {
    tools: {},
  },
});

// Configuration des outils MCP (version simplifiée pour test)
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "save_memory",
        description: "Sauvegarde générale dans la mémoire",
        inputSchema: {
          type: "object",
          properties: {
            what_we_did: { type: "string", description: "Description de l'action" }
          },
          required: ["what_we_did"]
        }
      },
      {
        name: "get_memory", 
        description: "Affiche la mémoire complète du projet",
        inputSchema: { type: "object", properties: {} }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    switch (name) {
      case "save_memory": {
        const memory = memoryService.loadMemory();
        memory.conversations.push({
          date: new Date().toISOString(),
          content: args.what_we_did
        });
        memoryService.saveMemory(memory);
        return {
          content: [{ type: "text", text: `✅ Mémoire sauvegardée : ${args.what_we_did}` }]
        };
      }
      
      case "get_memory": {
        const memory = memoryService.loadMemory();
        const summary = `🧠 **Mémoire Intelligente du Projet JinaScraper**

📊 **Statistiques Globales:**
• Conversations: ${memory.conversations?.length || 0}
• Changements techniques: ${memory.technical_changes?.length || 0}
• Auto-détections: ${memory.auto_detected_changes?.length || 0}
• Métriques performance: ${memory.performance_metrics?.length || 0}

📝 **Conversations récentes:**
${(memory.conversations || []).slice(-3).map(conv => 
  `• ${new Date(conv.date).toLocaleDateString()} : ${conv.content}`
).join('\n')}

🤖 **Surveillance:** ❌ Inactive`;
        
        return {
          content: [{ type: "text", text: summary }]
        };
      }
      
      default:
        return {
          content: [{ type: "text", text: `❌ Outil inconnu: ${name}` }]
        };
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `❌ Erreur: ${error.message}` }]
    };
  }
});

async function main() {
  // Mode test : arrêt automatique après vérification
  if (process.argv.includes('--test')) {
    console.log('🧪 MODE TEST - Serveur MCP mémoire refactorisé...');
    
    try {
      const memory = memoryService.loadMemory();
      console.log(`✅ Mémoire chargée : ${memory.conversations?.length || 0} conversations`);
      console.log(`✅ Projet root détecté : ${memoryService.projectRoot}`);
      console.log(`✅ Fichier mémoire : ${memoryService.memoryFile}`);
      
      // Test de sauvegarde
      const testMemory = memoryService.loadMemory();
      testMemory.conversations.push({
        date: new Date().toISOString(),
        content: 'Test serveur MCP refactorisé'
      });
      memoryService.saveMemory(testMemory);
      console.log('✅ Sauvegarde testée avec succès');
      
      console.log('🎉 Serveur MCP refactorisé fonctionne correctement !');
      process.exit(0);
    } catch (error) {
      console.error('❌ Erreur lors du test :', error.message);
      process.exit(1);
    }
  }
  
  // Mode normal : serveur MCP actif
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('🧠 Intelligent Memory System (Fixed) démarré !');
  
  // Gestion propre de l'arrêt
  process.on('SIGINT', () => {
    console.error('🛑 Arrêt du serveur MCP mémoire...');
    process.exit(0);
  });
}

main().catch(console.error);