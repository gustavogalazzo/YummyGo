/*
 * Lógica para autocompletar endereço e animações.
 */

document.addEventListener('DOMContentLoaded', function () {
  // --- 1. LÓGICA DO VIACEP ---
  const cepInput = document.getElementById('cep')

  // SÓ EXECUTA SE O CAMPO CEP EXISTIR NA PÁGINA
  if (cepInput) {
    cepInput.addEventListener('blur', function () {
      const cep = cepInput.value.replace(/\D/g, '')
      if (cep.length === 8) {
        fetchViaCEP(cep)
      } else {
        clearAddressForm()
      }
    })
  }

  // --- 2. INICIALIZA A ANIMAÇÃO ---
  initAnimations()
})

/**
 * Faz a chamada (fetch) à API do ViaCEP.
 */
function fetchViaCEP(cep) {
  const url = `https://viacep.com.br/ws/${cep}/json/`

  fetch(url)
    .then(response => response.json())
    .then(data => {
      if (data.erro) {
        alert('CEP não encontrado. Verifique o número.')
        clearAddressForm()
      } else {
        fillAddressForm(data)
      }
    })
    .catch(error => {
      console.error('Erro ao buscar CEP:', error)
    })
}

function fillAddressForm(data) {
  if (document.getElementById('rua'))
    document.getElementById('rua').value = data.logradouro
  if (document.getElementById('bairro'))
    document.getElementById('bairro').value = data.bairro
  if (document.getElementById('cidade'))
    document.getElementById('cidade').value = data.localidade
  if (document.getElementById('uf'))
    document.getElementById('uf').value = data.uf
  if (document.getElementById('numero'))
    document.getElementById('numero').focus()
}

function clearAddressForm() {
  if (document.getElementById('rua')) document.getElementById('rua').value = ''
  if (document.getElementById('bairro'))
    document.getElementById('bairro').value = ''
  if (document.getElementById('cidade'))
    document.getElementById('cidade').value = ''
  if (document.getElementById('uf')) document.getElementById('uf').value = ''
}

// --- FUNÇÃO TYPEWRITER ---
function typeWriter(element, text, speed) {
  let i = 0
  element.innerHTML = ''

  // Torna visível antes de começar
  element.style.visibility = 'visible'

  function typing() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i)
      i++
      setTimeout(typing, speed)
    } else {
      element.classList.remove('typing-cursor')
    }
  }
  typing()
}

// --- FUNÇÃO DE INICIALIZAÇÃO ---
function initAnimations() {
  const titleElement = document.getElementById('animated-title')

  if (titleElement) {
    const fullText = titleElement.getAttribute('data-fulltext')
    titleElement.classList.add('typing-cursor')
    typeWriter(titleElement, fullText, 50)
  }
}
