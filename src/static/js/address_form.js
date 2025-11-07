/*
 * Lógica para autocompletar o formulário de endereço
 * usando a API do ViaCEP.
 */

// 1. "Ouvir" o evento 'DOMContentLoaded'
// Isto garante que o nosso script só corre *depois*
// de todo o HTML ter sido carregado.
document.addEventListener('DOMContentLoaded', function () {
  // 2. Encontrar o campo do CEP pelo 'id' que demos a ele
  const cepInput = document.getElementById('cep')

  // 3. Adicionar um "ouvinte de evento" (event listener)
  // O evento 'blur' acontece quando o utilizador *sai* do campo.
  cepInput.addEventListener('blur', function () {
    // Pega o valor do CEP e remove hífens/pontos
    const cep = cepInput.value.replace(/\D/g, '')

    // 4. Verifica se o CEP tem 8 dígitos
    if (cep.length === 8) {
      // CEP válido, vamos buscar os dados!
      fetchViaCEP(cep)
    } else {
      // CEP inválido (ou vazio)
      clearAddressForm()
    }
  })
})

/**
 * Faz a chamada (fetch) à API do ViaCEP.
 */
function fetchViaCEP(cep) {
  const url = `https://viacep.com.br/ws/${cep}/json/`

  // 5. Faz a chamada à API
  fetch(url)
    .then(response => response.json()) // Converte a resposta para JSON
    .then(data => {
      // 6. Temos os dados! Vamos verificar se deu certo.
      if (data.erro) {
        // O ViaCEP respondeu, mas disse que este CEP não existe
        alert('CEP não encontrado. Verifique o número.')
        clearAddressForm()
      } else {
        // SUCESSO! Vamos preencher o formulário.
        fillAddressForm(data)
      }
    })
    .catch(error => {
      // Erro na chamada (ex: sem internet)
      console.error('Erro ao buscar CEP:', error)
      alert('Não foi possível buscar o CEP. Tente novamente.')
    })
}

/**
 * Preenche os campos do formulário com os dados do ViaCEP.
 */
function fillAddressForm(data) {
  document.getElementById('rua').value = data.logradouro
  document.getElementById('bairro').value = data.bairro
  document.getElementById('cidade').value = data.localidade
  document.getElementById('uf').value = data.uf

  // (Opcional) Foca no campo "número" para o utilizador
  document.getElementById('numero').focus()
}

/**
 * Limpa os campos (caso o CEP seja inválido ou não encontrado).
 */
function clearAddressForm() {
  document.getElementById('rua').value = ''
  document.getElementById('bairro').value = ''
  document.getElementById('cidade').value = ''
  document.getElementById('uf').value = ''
}

// --- FUNÇÃO TYPEWRITER ---
function typeWriter(element, text, speed) {
  let i = 0
  element.innerHTML = ''

  function typing() {
    if (i < text.length) {
      element.innerHTML += text.charAt(i)
      i++
      setTimeout(typing, speed)
    } else {
      // Quando terminar, remove a classe para garantir que o texto fica visível
      element.classList.remove('typing-cursor')
    }
  }
  typing()
}

// --- FUNÇÃO DE INICIALIZAÇÃO ---
function initAnimations() {
  const titleElement = document.getElementById('animated-title')

  if (titleElement) {
    // O fullText é lido do atributo data-fulltext no HTML
    const fullText = titleElement.getAttribute('data-fulltext')

    // Adiciona um cursor piscando (simulação CSS)
    titleElement.classList.add('typing-cursor')

    // Aplica a animação
    typeWriter(titleElement, fullText, 50)
  }
}

// 2. Chama a função de inicialização assim que o script é lido
document.addEventListener('DOMContentLoaded', initAnimations)
