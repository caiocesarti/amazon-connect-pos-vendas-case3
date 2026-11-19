#!/usr/bin/env node
/**
 * Injetor Node.js Multiplataforma do Widget do Amazon Connect (EletroLar Varejo - Case 3)
 * Compatível com o runtime padrão de build da Vercel.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const LOCAL_SNIPPET = path.join(ROOT, 'landing', 'widget-snippet.local.html');
const INDEX_FILE = path.join(ROOT, 'landing', 'index.html');
const LOADER_FILE = path.join(ROOT, 'landing', 'connect-widget-loader.js');
const PLACEHOLDER = '<!-- AMAZON_CONNECT_WIDGET_PLACEHOLDER -->';
const SCRIPT_TAG = '<script src="./connect-widget-loader.js" defer></script>';
const LIMIT = parseInt(process.env.MAX_WIDGET_MESSAGES_PER_VISITOR || '30', 10);

function obterSnippet() {
  const envVars = ['CONNECT_WIDGET_SNIPPET3', 'CONNECT_WIDGET_SNIPPET'];
  for (const v of envVars) {
    const val = (process.env[v] || '').trim();
    if (val) return val;
  }
  if (fs.existsSync(LOCAL_SNIPPET)) {
    const txt = fs.readFileSync(LOCAL_SNIPPET, 'utf8').trim();
    if (txt) return txt;
  }
  return null;
}

function gerarLoaderFinOps(snippet, limite) {
  let corpoJs = snippet.replace(/<\/?script[^>]*>/gi, '').trim();
  corpoJs = corpoJs.replace(/(?<![\w$.])s\s*=\s*d\.createElement/g, 'var s=d.createElement');

  if (!corpoJs.includes('customerDisplayName')) {
    corpoJs += `\n  amazon_connect('customerDisplayName', function(callback) {
    callback('Cliente EletroLar');
  });`;
  }

  if (!corpoJs.includes('customChatInitiateAttributes')) {
    corpoJs += `\n  amazon_connect('customChatInitiateAttributes', {
    pv_origem: 'landing',
    pv_canal: 'CHAT'
  });`;
  }

  return `/* ==========================================================================
   PROTEÇÃO FINOPS & ANTI-BOT (LIMITE DE ${limite} MENSAGENS POR VISITANTE)
   EletroLar Varejo — Central de Pós-Venda e Suporte de Eletrodomésticos (Case 3)
   ========================================================================== */
(function() {
  'use strict';
  var MAX_MSG = ${limite};
  var STORAGE_KEY = 'pv_aws_connect_msg_count_v1';

  // 1. Bloqueia crawlers e navegadores headless automatizados
  if (navigator.webdriver) {
    console.warn('[FinOps Guard] Automação detectada (navigator.webdriver). Widget AWS desativado; utilize o Simulador Local.');
    return;
  }

  // 2. Verifica cota de mensagens por visitante no navegador
  var usadas = parseInt(localStorage.getItem(STORAGE_KEY) || '0', 10);
  if (usadas >= MAX_MSG) {
    console.warn('[FinOps Guard] Limite de ' + MAX_MSG + ' mensagens atingido neste navegador para proteção do Free Tier.');
    return;
  }

  // 3. Contabiliza envios de mensagens até o limite de ${limite}
  window.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      var atual = parseInt(localStorage.getItem(STORAGE_KEY) || '0', 10) + 1;
      localStorage.setItem(STORAGE_KEY, String(atual));
    }
  }, true);

  // 4. Inicializa o Communications Widget Oficial do Amazon Connect
  ${corpoJs}
})();
`;
}

function executar() {
  const snippet = obterSnippet();
  if (!snippet) {
    console.log('[INFO] Nenhum snippet encontrado em CONNECT_WIDGET_SNIPPET3 nem em landing/widget-snippet.local.html.');
    console.log('Mantendo landing/index.html no modo de pré-visualização interativa limpa.');
    return;
  }

  let indexHtml = fs.readFileSync(INDEX_FILE, 'utf8');
  const loaderJs = gerarLoaderFinOps(snippet, LIMIT);
  fs.writeFileSync(LOADER_FILE, loaderJs, 'utf8');

  if (indexHtml.includes(PLACEHOLDER)) {
    indexHtml = indexHtml.replace(PLACEHOLDER, SCRIPT_TAG);
    fs.writeFileSync(INDEX_FILE, indexHtml, 'utf8');
  }

  console.log(`[WIDGET] OK - Snippet do Amazon Connect compilado com sucesso (Proteção FinOps: máx. ${LIMIT} msgs/visitante).`);
}

executar();
