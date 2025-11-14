/*
 * Lógica de Validação de Força de Senha (Password Strength)
 */

document.addEventListener('DOMContentLoaded', function () {
  const passwordField = document.getElementById('password-field')
  const feedbackDiv = document.getElementById('password-feedback')
  const requirementsList = document.getElementById('password-requirements')

  if (!passwordField || !requirementsList) {
    return // Sai se os elementos não existirem na página (segurança)
  }

  // Definição das regras de segurança
  const rules = [
    { regex: /.{8,}/, message: 'Pelo menos 8 caracteres' },
    { regex: /[A-Z]/, message: 'Pelo menos 1 letra maiúscula' },
    { regex: /[a-z]/, message: 'Pelo menos 1 letra minúscula' },
    { regex: /\d/, message: 'Pelo menos 1 número' },
    { regex: /[^A-Za-z0-9]/, message: 'Pelo menos 1 símbolo (ex: !, @, #)' }
  ]

  // Adiciona os event listeners
  passwordField.addEventListener('input', checkPasswordStrength)
  passwordField.addEventListener('focus', toggleRequirements)
  passwordField.addEventListener('blur', toggleRequirements)

  // Função para mostrar/esconder a lista de requisitos
  function toggleRequirements() {
    requirementsList.style.display =
      passwordField === document.activeElement || passwordField.value.length > 0
        ? 'block'
        : 'none'
  }

  // Função principal de verificação
  function checkPasswordStrength() {
    const password = passwordField.value
    let score = 0 // Contagem de regras cumpridas

    requirementsList.innerHTML = '' // Limpa o feedback anterior

    // 1. Verifica cada regra e atualiza o feedback visual
    rules.forEach(rule => {
      const isMet = rule.regex.test(password)
      const listItem = document.createElement('li')

      // Aplica o estilo (verde ou cinzento)
      listItem.className = isMet ? 'text-success' : 'text-muted'

      // Adiciona o ícone de check/X
      listItem.innerHTML = `<i class="fas ${
        isMet ? 'fa-check-circle' : 'fa-times-circle'
      } me-2"></i> ${rule.message}`

      requirementsList.appendChild(listItem)

      if (isMet) {
        score++
      }
    })

    // 2. Calcula a força e atualiza a barra de progresso
    const strength = Math.round((score / rules.length) * 100)
    updateProgressBar(strength)
  }

  // Função para atualizar a barra de progresso
  function updateProgressBar(strength) {
    const progressBar = document.getElementById('password-progress')

    // Define a cor da barra
    let colorClass = 'bg-danger'
    if (strength >= 80) {
      colorClass = 'bg-success'
    } else if (strength >= 50) {
      colorClass = 'bg-warning'
    }

    // Atualiza a barra
    progressBar.style.width = strength + '%'
    progressBar.className = `progress-bar ${colorClass}`
  }

  // Inicializa a barra ao carregar a página
  checkPasswordStrength()
})
