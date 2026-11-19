/**
 * EletroLar Varejo — Central de Pós-Venda e Suporte Técnico
 * Controles de acessibilidade, buscador de assistências autorizadas e integração com o chat.
 */

(function () {
  'use strict';

  const ASSISTENCIAS_AUTORIZADAS = [
    {
      id_unidade: 'AST-SP-01',
      nome_fantasia: 'TecnoLar Paulista — Assistência Autorizada Central',
      cidade: 'São Paulo',
      uf: 'SP',
      cep_inicio: '01000000',
      cep_fim: '03999999',
      faixa_cep_label: '01000-000 a 03999-999',
      endereco: 'Av. Paulista, 1842, Conj. 14, Bela Vista — São Paulo/SP',
      telefone: '(11) 3003-4010',
      horario_atendimento: 'Seg a Sex das 08h às 18h | Sáb das 08h às 13h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO', 'AR_CONDICIONADO'],
      especialidades_label: 'Lavadoras, Geladeiras, Micro-ondas, Fogões e Ar Split'
    },
    {
      id_unidade: 'AST-SP-02',
      nome_fantasia: 'EletroService Sul — Unidade Moema',
      cidade: 'São Paulo',
      uf: 'SP',
      cep_inicio: '04000000',
      cep_fim: '05999999',
      faixa_cep_label: '04000-000 a 05999-999',
      endereco: 'Av. Ibirapuera, 2907, Loja 12, Moema — São Paulo/SP',
      telefone: '(11) 3003-4022',
      horario_atendimento: 'Seg a Sex das 08h30 às 18h30 | Sáb das 09h às 13h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO', 'AR_CONDICIONADO'],
      especialidades_label: 'Linha Branca Completa e Climatização'
    },
    {
      id_unidade: 'AST-SP-03',
      nome_fantasia: 'MasterTec Oeste — Autorizada Osasco',
      cidade: 'Osasco',
      uf: 'SP',
      cep_inicio: '06000000',
      cep_fim: '06999999',
      faixa_cep_label: '06000-000 a 06999-999',
      endereco: 'Av. dos Autonomistas, 2500, Sala 108, Vila Yara — Osasco/SP',
      telefone: '(11) 3681-9015',
      horario_atendimento: 'Seg a Sex das 08h às 17h30 | Sáb das 08h às 12h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO', 'AR_CONDICIONADO'],
      especialidades_label: 'Lavadoras, Geladeiras, Micro-ondas, Fogões e Ar Split'
    },
    {
      id_unidade: 'AST-SP-04',
      nome_fantasia: 'Campinas EletroCare — Autorizada Linha Branca',
      cidade: 'Campinas',
      uf: 'SP',
      cep_inicio: '13000000',
      cep_fim: '13999999',
      faixa_cep_label: '13000-000 a 13999-999',
      endereco: 'Av. Francisco Glicério, 1420, Centro — Campinas/SP',
      telefone: '(19) 3231-5500',
      horario_atendimento: 'Seg a Sex das 08h às 18h | Sáb das 08h às 12h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO'],
      especialidades_label: 'Lavadoras, Geladeiras, Micro-ondas e Fogões'
    },
    {
      id_unidade: 'AST-BA-01',
      nome_fantasia: 'BahiaTec EletroLar — Caminho das Árvores',
      cidade: 'Salvador',
      uf: 'BA',
      cep_inicio: '40000000',
      cep_fim: '42699999',
      faixa_cep_label: '40000-000 a 42699-999',
      endereco: 'Av. Tancredo Neves, 1632, Caminho das Árvores — Salvador/BA',
      telefone: '(71) 3341-8800',
      horario_atendimento: 'Seg a Sex das 08h às 18h | Sáb das 08h às 13h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO', 'AR_CONDICIONADO'],
      especialidades_label: 'Linha Branca Completa e Climatização'
    },
    {
      id_unidade: 'AST-BA-02',
      nome_fantasia: 'Litoral Norte Service — Vilas do Atlântico',
      cidade: 'Lauro de Freitas',
      uf: 'BA',
      cep_inicio: '42700000',
      cep_fim: '42799999',
      faixa_cep_label: '42700-000 a 42799-999',
      endereco: 'Av. Santos Dumont, km 4,5, Loja 06 — Lauro de Freitas/BA',
      telefone: '(71) 3379-4200',
      horario_atendimento: 'Seg a Sex das 08h às 17h30 | Sáb das 08h às 12h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'AR_CONDICIONADO'],
      especialidades_label: 'Lavadoras, Geladeiras, Micro-ondas e Ar Split'
    },
    {
      id_unidade: 'AST-BA-03',
      nome_fantasia: 'SertãoFrio & Lavadoras — Feira de Santana',
      cidade: 'Feira de Santana',
      uf: 'BA',
      cep_inicio: '44000000',
      cep_fim: '44199999',
      faixa_cep_label: '44000-000 a 44199-999',
      endereco: 'Av. Getúlio Vargas, 2150, Centro — Feira de Santana/BA',
      telefone: '(75) 3623-7100',
      horario_atendimento: 'Seg a Sex das 08h às 18h | Sáb das 08h às 12h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO'],
      especialidades_label: 'Lavadoras, Geladeiras, Micro-ondas e Fogões'
    },
    {
      id_unidade: 'AST-RJ-01',
      nome_fantasia: 'CariocaTec Eletro — Unidade Botafogo',
      cidade: 'Rio de Janeiro',
      uf: 'RJ',
      cep_inicio: '20000000',
      cep_fim: '23999999',
      faixa_cep_label: '20000-000 a 23999-999',
      endereco: 'Rua Voluntários da Pátria, 340, Loja B, Botafogo — Rio de Janeiro/RJ',
      telefone: '(21) 2541-9900',
      horario_atendimento: 'Seg a Sex das 08h30 às 18h | Sáb das 09h às 13h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO', 'AR_CONDICIONADO'],
      especialidades_label: 'Linha Branca Completa e Climatização'
    },
    {
      id_unidade: 'AST-MG-01',
      nome_fantasia: 'MinasLar Assistência Técnica — Savassi',
      cidade: 'Belo Horizonte',
      uf: 'MG',
      cep_inicio: '30000000',
      cep_fim: '31999999',
      faixa_cep_label: '30000-000 a 31999-999',
      endereco: 'Av. do Contorno, 6283, Savassi — Belo Horizonte/MG',
      telefone: '(31) 3281-6060',
      horario_atendimento: 'Seg a Sex das 08h às 18h | Sáb das 08h às 12h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO', 'AR_CONDICIONADO'],
      especialidades_label: 'Linha Branca Completa e Climatização'
    },
    {
      id_unidade: 'AST-PR-01',
      nome_fantasia: 'SulTec Eletrodomésticos — Unidade Batel',
      cidade: 'Curitiba',
      uf: 'PR',
      cep_inicio: '80000000',
      cep_fim: '82999999',
      faixa_cep_label: '80000-000 a 82999-999',
      endereco: 'Av. Sete de Setembro, 4120, Batel — Curitiba/PR',
      telefone: '(41) 3322-4500',
      horario_atendimento: 'Seg a Sex das 08h às 18h | Sáb das 08h30 às 12h30',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO'],
      especialidades_label: 'Lavadoras, Geladeiras, Micro-ondas e Fogões'
    },
    {
      id_unidade: 'AST-RS-01',
      nome_fantasia: 'GaúchaTec Linha Branca — Floresta',
      cidade: 'Porto Alegre',
      uf: 'RS',
      cep_inicio: '90000000',
      cep_fim: '91999999',
      faixa_cep_label: '90000-000 a 91999-999',
      endereco: 'Av. Cristóvão Colombo, 1850, Floresta — Porto Alegre/RS',
      telefone: '(51) 3346-7800',
      horario_atendimento: 'Seg a Sex das 08h30 às 18h | Sáb das 09h às 12h30',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO', 'AR_CONDICIONADO'],
      especialidades_label: 'Linha Branca Completa e Climatização'
    },
    {
      id_unidade: 'AST-DF-01',
      nome_fantasia: 'PlanaltoTec Autorizada — Asa Sul',
      cidade: 'Brasília',
      uf: 'DF',
      cep_inicio: '70000000',
      cep_fim: '72999999',
      faixa_cep_label: '70000-000 a 72999-999',
      endereco: 'CLS 405, Bloco C, Loja 18, Asa Sul — Brasília/DF',
      telefone: '(61) 3244-8100',
      horario_atendimento: 'Seg a Sex das 08h às 18h | Sáb das 08h às 12h',
      especialidades: ['LAVADORA', 'GELADEIRA', 'MICROONDAS', 'FOGAO', 'AR_CONDICIONADO'],
      especialidades_label: 'Linha Branca Completa e Climatização'
    }
  ];

  // 1. Controles de Acessibilidade
  const htmlEl = document.documentElement;
  let currentFontSize = parseInt(localStorage.getItem('pv_font_size') || '18', 10);

  function aplicarTamanhoFonte(size) {
    currentFontSize = Math.min(24, Math.max(16, size));
    htmlEl.style.setProperty('--font-size-base', currentFontSize + 'px');
    localStorage.setItem('pv_font_size', String(currentFontSize));
  }

  aplicarTamanhoFonte(currentFontSize);

  document.getElementById('btn-font-decrease')?.addEventListener('click', () => aplicarTamanhoFonte(currentFontSize - 2));
  document.getElementById('btn-font-reset')?.addEventListener('click', () => aplicarTamanhoFonte(18));
  document.getElementById('btn-font-increase')?.addEventListener('click', () => aplicarTamanhoFonte(currentFontSize + 2));

  const btnTheme = document.getElementById('btn-theme-toggle');
  const themeText = document.getElementById('theme-text');

  function aplicarTema(tema, salvarPreferencia = false) {
    htmlEl.setAttribute('data-theme', tema);
    if (salvarPreferencia) {
      localStorage.setItem('pv_theme_user', tema);
    }
    const isDark = tema === 'dark';
    btnTheme?.setAttribute('aria-pressed', String(isDark));
    if (themeText) themeText.textContent = isDark ? 'Modo Claro' : 'Alto Contraste';
    const headerLogo = document.getElementById('header-logo-img');
    if (headerLogo) {
      headerLogo.setAttribute('src', isDark ? './assets/logo-eletrolar-footer.svg' : './assets/logo-eletrolar.svg');
    }
  }

  const temaSalvo = localStorage.getItem('pv_theme_user');
  aplicarTema(temaSalvo === 'dark' ? 'dark' : 'light');

  btnTheme?.addEventListener('click', () => {
    const atual = htmlEl.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    aplicarTema(atual, true);
  });

  // 2. Diretório Interativo de Assistências Técnicas Autorizadas (exibe até 6 cartões para manter o layout clean)
  const listaAstEl = document.getElementById('lista-assistencias');
  const statusFiltroEl = document.getElementById('status-filtro');
  const selectEsp = document.getElementById('select-especialidade');
  const selectCid = document.getElementById('select-cidade');
  const inputCep = document.getElementById('input-cep');
  const formFiltro = document.getElementById('form-filtro-guia');
  const btnLimpar = document.getElementById('btn-limpar-filtro');

  function extrairCepLimpo(valor) {
    const digitos = (valor || '').replace(/\D/g, '');
    return digitos.length === 8 ? digitos : '';
  }

  function renderizarAssistencias(catFiltro, cidFiltro, cepFiltro) {
    if (!listaAstEl) return;

    const cep8 = extrairCepLimpo(cepFiltro);
    const filtradas = ASSISTENCIAS_AUTORIZADAS.filter((u) => {
      const okCat = !catFiltro || u.especialidades.includes(catFiltro);
      const okCid = !cidFiltro || u.cidade === cidFiltro;
      let okCep = true;
      if (cep8) {
        const num = parseInt(cep8, 10);
        okCep = num >= parseInt(u.cep_inicio, 10) && num <= parseInt(u.cep_fim, 10);
      }
      return okCat && okCid && okCep;
    });

    if (statusFiltroEl) {
      if (filtradas.length === 0) {
        statusFiltroEl.textContent =
          'Não encontramos posto autorizado presencial para o CEP ou município informado. Solicite atendimento pelo Chat.';
      } else {
        statusFiltroEl.textContent = `Mostrando ${Math.min(filtradas.length, 6)} de ${filtradas.length} assistência(s) autorizada(s):`;
      }
    }

    listaAstEl.innerHTML = '';

    if (filtradas.length === 0) {
      const localBuscado = cep8 || cidFiltro || 'minha região';
      const emptyCard = document.createElement('div');
      emptyCard.className = 'assistencia-card';
      emptyCard.innerHTML = `
        <div>
          <h3 class="assistencia-name">Atendimento Especial para sua Região</h3>
          <p class="assistencia-meta" style="margin-top:0.5rem">
            Não há posto físico diretamente em <strong>${localBuscado}</strong>, mas nossa equipe agenda a coleta domiciliar gratuita para você pelo chat.
          </p>
        </div>
        <button type="button" class="btn btn-primary" data-chat-prefill="Preciso de assistência para o CEP ${localBuscado}">
          Falar com Especialista no Chat
        </button>
      `;
      listaAstEl.appendChild(emptyCard);
      return;
    }

    filtradas.slice(0, 6).forEach((u) => {
      const card = document.createElement('article');
      card.className = 'assistencia-card';
      card.innerHTML = `
        <div>
          <div class="assistencia-header">
            <span class="assistencia-badge">${u.cidade} — ${u.uf}</span>
            <span class="assistencia-id">CEP ${u.faixa_cep_label}</span>
          </div>
          <h3 class="assistencia-name">${u.nome_fantasia}</h3>
          <div class="assistencia-meta">
            <span><strong>Endereço:</strong> ${u.endereco}</span>
            <span><strong>Telefone:</strong> ${u.telefone}</span>
            <span><strong>Atende:</strong> ${u.especialidades_label}</span>
          </div>
        </div>
        <div class="assistencia-slots">
          Horário: <strong>${u.horario_atendimento}</strong>
        </div>
        <button type="button" class="btn btn-primary" data-chat-prefill="Quero atendimento na autorizada de ${u.cidade}">
          Solicitar pelo Chat
        </button>
      `;
      listaAstEl.appendChild(card);
    });
  }

  renderizarAssistencias('', '', '');

  formFiltro?.addEventListener('submit', (e) => {
    e.preventDefault();
    renderizarAssistencias(selectEsp?.value || '', selectCid?.value || '', inputCep?.value || '');
  });

  selectEsp?.addEventListener('change', () =>
    renderizarAssistencias(selectEsp.value, selectCid?.value || '', inputCep?.value || '')
  );
  selectCid?.addEventListener('change', () =>
    renderizarAssistencias(selectEsp?.value || '', selectCid.value, inputCep?.value || '')
  );
  inputCep?.addEventListener('input', () => {
    if (extrairCepLimpo(inputCep.value).length === 8 || inputCep.value.trim() === '') {
      renderizarAssistencias(selectEsp?.value || '', selectCid?.value || '', inputCep.value);
    }
  });

  btnLimpar?.addEventListener('click', () => {
    if (selectEsp) selectEsp.value = '';
    if (selectCid) selectCid.value = '';
    if (inputCep) inputCep.value = '';
    renderizarAssistencias('', '', '');
  });

  document.querySelectorAll('[data-filter-esp]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const esp = btn.getAttribute('data-filter-esp') || '';
      if (selectEsp) selectEsp.value = esp;
      renderizarAssistencias(esp, selectCid?.value || '', inputCep?.value || '');
      document.getElementById('diretorio-assistencias')?.scrollIntoView({ behavior: 'smooth' });
    });
  });

  document.querySelectorAll('[data-quick-esp]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const esp = btn.getAttribute('data-quick-esp') || '';
      const cid = btn.getAttribute('data-quick-cid') || '';
      if (selectEsp) selectEsp.value = esp;
      if (selectCid) selectCid.value = cid;
      renderizarAssistencias(esp, cid, '');
      document.getElementById('diretorio-assistencias')?.scrollIntoView({ behavior: 'smooth' });
    });
  });

  // 3. Integração com o Widget do Amazon Connect
  const chatModal = document.getElementById('chat-preview-modal');
  const floatingChatBtn = document.getElementById('floating-chat-btn');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-preview-form');
  const chatInput = document.getElementById('chat-input');

  const observerConnect = new MutationObserver(() => {
    const connectIframe = document.querySelector('iframe[id^="amazon-connect"], [id^="amazon-connect-chat-widget"]');
    if (connectIframe && floatingChatBtn) {
      floatingChatBtn.hidden = true;
      observerConnect.disconnect();
    }
  });
  observerConnect.observe(document.body, { childList: true, subtree: true });

  function acionarWidgetConnectOuPreview(mensagemInicial) {
    const connectLauncher = document.querySelector(
      '#amazon-connect-open-widget-button, button[id*="amazon-connect-open"], [id^="amazon-connect-chat-widget"] button, .amazon-connect-chat-launcher, iframe[title*="Amazon Connect"]'
    );
    if (connectLauncher && typeof connectLauncher.click === 'function') {
      connectLauncher.click();
      return;
    }

    if (chatModal) {
      chatModal.hidden = false;
      if (floatingChatBtn) floatingChatBtn.hidden = true;
      chatInput?.focus();
      if (mensagemInicial) {
        processarMensagemPreview(mensagemInicial);
      }
    }
  }

  document.querySelectorAll('.btn-open-chat').forEach((btn) => {
    btn.addEventListener('click', () => acionarWidgetConnectOuPreview(''));
  });

  document.querySelectorAll('[data-chat-trigger]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const msg = btn.getAttribute('data-chat-trigger') || '';
      acionarWidgetConnectOuPreview(msg);
    });
  });

  document.addEventListener('click', (e) => {
    const target = e.target.closest('[data-chat-prefill]');
    if (target) {
      const msg = target.getAttribute('data-chat-prefill') || '';
      acionarWidgetConnectOuPreview(msg);
    }
  });

  btnCloseModal?.addEventListener('click', () => {
    if (chatModal) chatModal.hidden = true;
  });

  function adicionarBolha(texto, autor) {
    if (!chatMessages) return;
    const div = document.createElement('div');
    div.className = `chat-bubble ${autor}`;
    if (autor === 'user') {
      div.textContent = texto;
    } else {
      div.innerHTML = texto;
    }
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function responderPosVendaLocal(entrada) {
    const txt = entrada.toLowerCase();

    if (
      txt.includes('fumaça') ||
      txt.includes('fumaca') ||
      txt.includes('queimado') ||
      txt.includes('choque') ||
      txt.includes('fogo') ||
      txt.includes('faísca')
    ) {
      return (
        '<strong>⚠️ Atenção à sua segurança:</strong> Por favor, desligue o aparelho da tomada imediatamente e não toque no equipamento.<br><br>' +
        '• <strong>Protocolo Prioritário:</strong> <code>PV-20261118-9911</code><br>' +
        '• Estou transferindo seu atendimento agora mesmo para um especialista da nossa equipe.'
      );
    }

    if (txt.includes('atendente') || txt.includes('humano') || txt.includes('pessoa') || txt.includes('especialista')) {
      return (
        'Claro! Já estou transferindo seu atendimento para um especialista da <strong>EletroLar</strong> (Protocolo <code>PV-20261118-7701</code>). ' +
        'Todas as informações da nossa conversa já foram encaminhadas para que você não precise repetir nada.'
      );
    }

    if (txt.includes('troca') || txt.includes('trocar') || txt.includes('devolver') || txt.includes('devolução') || txt.includes('arrependimento')) {
      return (
        '<strong>Solicitação de Troca / Devolução registrada com sucesso!</strong><br><br>' +
        '• <strong>Protocolo:</strong> <code>PV-20261118-3390</code><br>' +
        '• <strong>Nota Fiscal:</strong> <code>NF-100203</code><br>' +
        '• <strong>Produto:</strong> Micro-ondas EletroLar Chef 32L Espelhado<br>' +
        '• <strong>Coleta domiciliar:</strong> Agendada em até 48h úteis.'
      );
    }

    if (
      txt.includes('defeito') ||
      txt.includes('parou de funcionar') ||
      txt.includes('garantia') ||
      txt.includes('não gela') ||
      txt.includes('nf-100')
    ) {
      return (
        '<strong>Garantia acionada com sucesso!</strong><br><br>' +
        '• <strong>Protocolo:</strong> <code>PV-20261118-4821</code><br>' +
        '• <strong>Produto:</strong> Lavadora EletroLar 12kg Turbo Inverter (Série <code>EL-LAV-2026-8841</code>)<br>' +
        '• <strong>Nota Fiscal:</strong> <code>NF-100201</code> — Garantia ativa até 14/11/2027<br>' +
        '• <strong>Autorizada:</strong> TecnoLar Paulista — Av. Paulista, 1842, São Paulo/SP<br>' +
        '• <strong>Contato:</strong> (11) 3003-4010 | Seg a Sex 08h–18h, Sáb 08h–13h'
      );
    }

    const cepMatch = txt.match(/\b(\d{5})[\s.-]?(\d{3})\b/);
    if (cepMatch) {
      const cep8 = cepMatch[1] + cepMatch[2];
      const num = parseInt(cep8, 10);
      const achada = ASSISTENCIAS_AUTORIZADAS.find(
        (u) => num >= parseInt(u.cep_inicio, 10) && num <= parseInt(u.cep_fim, 10)
      );
      if (!achada) {
        return (
          `Não encontramos um posto presencial diretamente no CEP <strong>${cepMatch[0]}</strong>. ` +
          `Gerei o protocolo <code>PV-20261118-6990</code> e estou transferindo você para nossa equipe agendar a coleta gratuita em domicílio.`
        );
      }
      return (
        `Encontrei a assistência técnica autorizada mais próxima para o CEP <strong>${cepMatch[0]}</strong>:<br><br>` +
        `• <strong>Autorizada:</strong> ${achada.nome_fantasia}<br>` +
        `• <strong>Endereço:</strong> ${achada.endereco}<br>` +
        `• <strong>Telefone:</strong> ${achada.telefone}<br>` +
        `• <strong>Horário:</strong> ${achada.horario_atendimento}`
      );
    }

    const cidAchada = ASSISTENCIAS_AUTORIZADAS.find((u) =>
      txt.includes(u.cidade.toLowerCase()) ||
      (u.cidade === 'São Paulo' && (txt.includes('sao paulo') || txt.includes('paulo'))) ||
      (u.cidade === 'Brasília' && txt.includes('brasilia'))
    );
    if (cidAchada) {
      return (
        `Encontrei a assistência técnica autorizada em <strong>${cidAchada.cidade}/${cidAchada.uf}</strong>:<br><br>` +
        `• <strong>Autorizada:</strong> ${cidAchada.nome_fantasia}<br>` +
        `• <strong>Endereço:</strong> ${cidAchada.endereco}<br>` +
        `• <strong>Telefone:</strong> ${cidAchada.telefone}<br>` +
        `• <strong>Horário:</strong> ${cidAchada.horario_atendimento}`
      );
    }

    return (
      'Por favor, informe se deseja <strong>acionar a garantia</strong> (modelo, série e nota fiscal), ' +
      '<strong>localizar uma assistência autorizada</strong> (informe seu CEP ou cidade) ou <strong>solicitar troca/devolução</strong>.'
    );
  }

  function processarMensagemPreview(msg) {
    if (!msg.trim()) return;
    adicionarBolha(msg, 'user');
    setTimeout(() => {
      adicionarBolha(responderPosVendaLocal(msg), 'bot');
    }, 280);
  }

  chatForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!chatInput) return;
    const msg = chatInput.value;
    chatInput.value = '';
    processarMensagemPreview(msg);
  });

  document.querySelectorAll('.quick-reply-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const utt = btn.getAttribute('data-utterance') || '';
      processarMensagemPreview(utt);
    });
  });
})();
