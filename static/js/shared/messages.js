// En static/js/shared/messages.js

// Variables globales
let currentConversationId = null;
let messagePollingInterval = null;
let typingTimeout = null;
let lastMessageId = 0;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeMessaging();
});

function initializeMessaging() {
    // Configurar búsqueda de contactos
    setupContactSearch();
    
    // Configurar búsqueda de conversaciones
    setupConversationSearch();
    
    // Configurar eventos de teclado
    setupKeyboardEvents();
    
    // Configurar auto-resize del textarea
    setupTextareaAutoResize();
    
    // Configurar envío de mensajes
    setupMessageSending();
    
    // Configurar polling de mensajes
    setupMessagePolling();
    
    console.log('Sistema de mensajería inicializado');
}

// Funciones de conversación
function openConversation(conversationId) {
    // Detener polling anterior
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
    }
    
    // Actualizar conversación actual
    currentConversationId = conversationId;
    
    // Marcar conversación como activa
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const activeConversation = document.querySelector(`[data-conversation-id="${conversationId}"]`);
    if (activeConversation) {
        activeConversation.classList.add('active');
    }
    
    // Mostrar área de conversación y ocultar pantalla de bienvenida
    showConversationArea();
    
    // Cargar mensajes
    loadMessages(conversationId);
    
    // Iniciar polling
    startMessagePolling();
    
    // Marcar mensajes como leídos
    markMessagesAsRead(conversationId);
}

function showConversationArea() {
    const welcomeScreen = document.getElementById('welcomeScreen');
    const conversationArea = document.getElementById('conversationArea');
    
    if (welcomeScreen) welcomeScreen.classList.add('d-none');
    if (conversationArea) conversationArea.classList.remove('d-none');
}

function showWelcomeScreen() {
    const welcomeScreen = document.getElementById('welcomeScreen');
    const conversationArea = document.getElementById('conversationArea');
    
    if (welcomeScreen) welcomeScreen.classList.remove('d-none');
    if (conversationArea) conversationArea.classList.add('d-none');
}

function backToConversations() {
    // Detener polling
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
    }
    
    // Limpiar conversación actual
    currentConversationId = null;
    
    // Quitar clase activa
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Mostrar pantalla de bienvenida
    showWelcomeScreen();
}

function loadMessages(conversationId) {
    fetch(`/accounts/messages/conversation/${conversationId}/messages/`)
    .then(response => response.json())
    .then(data => {
        displayMessages(data.messages);
        updateConversationInfo(data.conversation);
        
        // Scroll al final
        scrollToBottom();
    })
    .catch(error => {
        console.error('Error cargando mensajes:', error);
        showNotification('Error al cargar mensajes', 'error');
    });
}

function displayMessages(messages) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    if (messages.length === 0) {
        messagesContainer.innerHTML = `
            <div class="no-messages">
                <i class="bi bi-chat-dots text-muted display-4"></i>
                <p class="text-muted mt-3">No hay mensajes aún</p>
                <p class="text-muted">¡Envía el primer mensaje!</p>
            </div>
        `;
        return;
    }
    
    const messagesHTML = messages.map(message => `
        <div class="message ${message.is_from_user ? 'sent' : 'received'}" data-message-id="${message.id}">
            <div class="message-content">
                <div class="message-text">${escapeHtml(message.content)}</div>
                <div class="message-meta">
                    <span class="message-time">${formatTime(message.created_at)}</span>
                    ${message.is_from_user ? `
                        <span class="message-status">
                            <i class="bi bi-${message.is_read ? 'check2-all text-primary' : 'check2'}" title="${message.is_read ? 'Leído' : 'Enviado'}"></i>
                        </span>
                    ` : ''}
                </div>
            </div>
            ${!message.is_from_user ? `
                <div class="message-avatar">
                    ${message.sender.avatar ? 
                        `<img src="${message.sender.avatar}" alt="${message.sender.full_name}">` :
                        `<div class="avatar-placeholder">${message.sender.full_name.charAt(0).toUpperCase()}</div>`
                    }
                </div>
            ` : ''}
        </div>
    `).join('');
    
    messagesContainer.innerHTML = messagesHTML;
    
    // Actualizar último mensaje ID
    if (messages.length > 0) {
        lastMessageId = Math.max(...messages.map(m => m.id));
    }
}

function updateConversationInfo(conversation) {
    document.getElementById('conversationName').textContent = conversation.name;
    document.getElementById('conversationStatus').textContent = conversation.participants_info;
    
    // Actualizar avatar
    const avatarContainer = document.getElementById('conversationAvatar');
    if (conversation.avatar) {
        avatarContainer.innerHTML = `<img src="${conversation.avatar}" alt="${conversation.name}">`;
    } else {
        avatarContainer.innerHTML = `<div class="avatar-placeholder">${conversation.name.charAt(0).toUpperCase()}</div>`;
    }
}

function startNewConversation(contactId) {
    const messageText = document.getElementById('newMessageText');
    const message = messageText ? messageText.value.trim() : '';
    
    if (!message) {
        const promptMessage = prompt('Escribe un mensaje para iniciar la conversación:');
        if (!promptMessage || !promptMessage.trim()) return;
        message = promptMessage.trim();
    }
    
    fetch('/accounts/messages/start/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            contact_id: contactId,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cerrar modal si existe
            const modal = bootstrap.Modal.getInstance(document.getElementById('newMessageModal'));
            if (modal) modal.hide();
            
            // Abrir conversación
            openConversation(data.conversation_id);
            
            // Recargar lista de conversaciones
            loadConversations();
        } else {
            showNotification(data.error || 'Error al iniciar conversación', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error al iniciar conversación', 'error');
    });
}

// Funciones de envío de mensajes
function setupMessageSending() {
    const messageForm = document.getElementById('messageForm');
    if (!messageForm) return;
    
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });
    
    // Enviar con Enter (pero permitir Shift+Enter para nueva línea)
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Indicador de escritura
        messageInput.addEventListener('input', function() {
            handleTyping();
        });
    }
}

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || !currentConversationId) return;
    
    // Deshabilitar input temporalmente
    messageInput.disabled = true;
    
    fetch(`/accounts/messages/conversation/${currentConversationId}/send/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            content: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Limpiar input
            messageInput.value = '';
            messageInput.style.height = 'auto';
            
            // Agregar mensaje a la vista
            addMessageToView(data.message);
            
            // Scroll al final
            scrollToBottom();
            
            // Actualizar lista de conversaciones
            updateConversationInList(data.conversation);
        } else {
            showNotification(data.error || 'Error al enviar mensaje', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error al enviar mensaje', 'error');
    })
    .finally(() => {
        messageInput.disabled = false;
        messageInput.focus();
    });
}

function addMessageToView(message) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    // Remover mensaje de "no hay mensajes" si existe
    const noMessages = messagesContainer.querySelector('.no-messages');
    if (noMessages) {
        noMessages.remove();
    }
    
    const messageHTML = `
        <div class="message sent" data-message-id="${message.id}">
            <div class="message-content">
                <div class="message-text">${escapeHtml(message.content)}</div>
                <div class="message-meta">
                    <span class="message-time">${formatTime(message.created_at)}</span>
                    <span class="message-status">
                        <i class="bi bi-check2" title="Enviado"></i>
                    </span>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    lastMessageId = message.id;
}

function updateConversationInList(conversation) {
    const conversationItem = document.querySelector(`[data-conversation-id="${conversation.id}"]`);
    if (conversationItem) {
        const lastMessageElement = conversationItem.querySelector('.last-message');
        const timeElement = conversationItem.querySelector('.conversation-time');
        
        if (lastMessageElement) {
            lastMessageElement.textContent = conversation.last_message_preview;
        }
        
        if (timeElement) {
            timeElement.textContent = formatTime(conversation.last_message_time);
        }
        
        // Mover conversación al principio
        const conversationsList = conversationItem.parentNode;
        conversationsList.insertBefore(conversationItem, conversationsList.firstChild);
    }
}

// Funciones de polling de mensajes
function setupMessagePolling() {
    // Solo iniciar si hay una conversación activa
    if (currentConversationId) {
        startMessagePolling();
    }
}

function startMessagePolling() {
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
    }
    
    messagePollingInterval = setInterval(() => {
        checkForNewMessages();
    }, 3000); // Verificar cada 3 segundos
}

function checkForNewMessages() {
    if (!currentConversationId) return;
    
    fetch(`/accounts/messages/conversation/${currentConversationId}/check-new/?last_id=${lastMessageId}`)
    .then(response => response.json())
    .then(data => {
        if (data.new_messages && data.new_messages.length > 0) {
            // Agregar nuevos mensajes
            data.new_messages.forEach(message => {
                addReceivedMessageToView(message);
            });
            
            // Actualizar último mensaje ID
            lastMessageId = Math.max(...data.new_messages.map(m => m.id));
            
            // Scroll al final
            scrollToBottom();
            
            // Marcar como leído
            markMessagesAsRead(currentConversationId);
        }
        
        // Actualizar estado de mensajes leídos
        if (data.read_updates && data.read_updates.length > 0) {
            updateMessageReadStatus(data.read_updates);
        }
    })
    .catch(error => {
        console.error('Error verificando mensajes:', error);
    });
}

function addReceivedMessageToView(message) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    const messageHTML = `
        <div class="message received" data-message-id="${message.id}">
            <div class="message-avatar">
                ${message.sender.avatar ? 
                    `<img src="${message.sender.avatar}" alt="${message.sender.full_name}">` :
                    `<div class="avatar-placeholder">${message.sender.full_name.charAt(0).toUpperCase()}</div>`
                }
            </div>
            <div class="message-content">
                <div class="message-text">${escapeHtml(message.content)}</div>
                <div class="message-meta">
                    <span class="message-time">${formatTime(message.created_at)}</span>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
}

function updateMessageReadStatus(readUpdates) {
    readUpdates.forEach(update => {
        const messageElement = document.querySelector(`[data-message-id="${update.message_id}"]`);
        if (messageElement) {
            const statusIcon = messageElement.querySelector('.message-status i');
            if (statusIcon) {
                statusIcon.className = 'bi bi-check2-all text-primary';
                statusIcon.title = 'Leído';
            }
        }
    });
}

function markMessagesAsRead(conversationId) {
    fetch(`/accounts/messages/conversation/${conversationId}/mark-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
}

// Funciones de contactos
function setupContactSearch() {
    const searchInput = document.getElementById('contactSearch');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            document.getElementById('searchResults').innerHTML = '';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            searchUsers(query);
        }, 300);
    });
}

function searchUsers(query) {
    console.log('Buscando usuarios con query:', query);
    
    fetch(`/accounts/messages/search-users/?q=${encodeURIComponent(query)}`)
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Datos recibidos:', data);
        displaySearchResults(data.users);
    })
    .catch(error => {
        console.error('Error en búsqueda:', error);
        showNotification('Error al buscar usuarios', 'error');
    });
}

function displaySearchResults(users) {
    const resultsContainer = document.getElementById('searchResults');
    if (users.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted text-center py-3">No se encontraron usuarios</p>';
        return;
    }
    
    const resultsHTML = users.map(user => `
        <div class="search-result-item d-flex align-items-center p-3 border rounded mb-2">
            <div class="avatar-sm me-3">
                ${user.avatar ? 
                    `<img src="${user.avatar}" alt="${user.full_name}" class="rounded-circle" width="40" height="40">` : 
                    `<div class="avatar-placeholder rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px; background: #007bff; color: white; font-weight: bold;">
                        ${user.full_name.charAt(0).toUpperCase()}
                    </div>`
                }
            </div>
            <div class="flex-grow-1">
                <div><strong>${user.full_name}</strong></div>
                <small class="text-muted">@${user.username}</small><br>
                <small class="text-muted">${user.user_type_name}</small>
            </div>
            <div>
                <button class="btn btn-primary btn-sm" onclick="selectUserAndStartChat(${user.id}, '${user.full_name}')">
                    <i class="bi bi-chat-dots me-1"></i>Chatear
                </button>
            </div>
        </div>
    `).join('');
    
    resultsContainer.innerHTML = resultsHTML;
}

function selectUserForMessage(userId, userName) {
    document.getElementById('selectedContactId').value = userId;
    document.getElementById('selectedContactName').textContent = userName;
    document.getElementById('contactSearch').value = '';
    document.getElementById('searchResults').innerHTML = '';
    document.getElementById('newMessageText').focus();
}

function selectUserAndStartChat(userId, userName) {
    // Pedir mensaje inicial
    const message = prompt(`Escribe un mensaje para iniciar la conversación con ${userName}:`);
    
    if (!message || !message.trim()) {
        return;
    }
    
    // Iniciar conversación directamente
    fetch('/accounts/messages/start/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            contact_id: userId,
            message: message.trim()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addContactModal'));
            if (modal) modal.hide();
            
            // Limpiar búsqueda
            document.getElementById('contactSearch').value = '';
            document.getElementById('searchResults').innerHTML = '';
            
            // Recargar la página para mostrar la nueva conversación
            window.location.reload();
            
            showNotification(`Conversación iniciada con ${userName}`, 'success');
        } else {
            showNotification(data.error || 'Error al iniciar conversación', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error al iniciar conversación', 'error');
    });
}

function sendContactRequest(userId) {
    fetch('/accounts/messages/add-contact/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ contact: userId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            document.getElementById('searchResults').innerHTML = '';
            document.getElementById('contactSearch').value = '';
            // Cierra el modal si quieres
            const modal = bootstrap.Modal.getInstance(document.getElementById('addContactModal'));
            if (modal) modal.hide();
            // Recarga contactos si es necesario
            loadContacts && loadContacts();
        } else {
            showNotification(data.error || 'Error al enviar solicitud', 'error');
        }
    })
    .catch(error => {
        showNotification('Error al enviar solicitud', 'error');
    });
}

function respondContactRequest(requestId, action) {
    fetch(`/accounts/messages/contact-request/${requestId}/respond/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            
            // Remover la solicitud de la vista
            const requestElement = document.querySelector(`[data-request-id="${requestId}"]`);
            if (requestElement) {
                requestElement.remove();
            }
            
            // Si es aceptación, recargar contactos
            if (action === 'accept') {
                loadContacts();
            }
        } else {
            showNotification(data.error || 'Error al responder solicitud', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error al responder solicitud', 'error');
    });
}

// Funciones de búsqueda de conversaciones
function setupConversationSearch() {
    const searchInput = document.getElementById('searchConversations');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        const conversations = document.querySelectorAll('.conversation-item');
        
        conversations.forEach(conversation => {
            const name = conversation.querySelector('.conversation-name').textContent.toLowerCase();
            const lastMessage = conversation.querySelector('.last-message');
            const lastMessageText = lastMessage ? lastMessage.textContent.toLowerCase() : '';
            
            if (name.includes(query) || lastMessageText.includes(query)) {
                conversation.style.display = 'block';
            } else {
                conversation.style.display = 'none';
            }
        });
    });
}

// Funciones de teclado
function setupKeyboardEvents() {
    // Atajos de teclado globales
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K para buscar
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('searchConversations');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape para cerrar modales
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
}

// Función para auto-resize del textarea
function setupTextareaAutoResize() {
    const textareas = document.querySelectorAll('.message-input');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });
    });
}

// Funciones de indicador de escritura
function handleTyping() {
    if (!currentConversationId) return;
    
    // Enviar indicador de que está escribiendo
    sendTypingIndicator();
    
    // Limpiar timeout anterior
    if (typingTimeout) {
        clearTimeout(typingTimeout);
    }
    
    // Después de 3 segundos de inactividad, dejar de mostrar "escribiendo"
    typingTimeout = setTimeout(() => {
        stopTypingIndicator();
    }, 3000);
}

function sendTypingIndicator() {
    fetch(`/accounts/messages/conversation/${currentConversationId}/typing/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
}

function stopTypingIndicator() {
    fetch(`/accounts/messages/conversation/${currentConversationId}/stop-typing/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
}

// Funciones de utilidad
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function loadConversations() {
    fetch('/accounts/messages/conversations/')
    .then(response => response.json())
    .then(data => {
        displayConversations(data.conversations);
    })
    .catch(error => {
        console.error('Error cargando conversaciones:', error);
    });
}

function loadContacts() {
    fetch('/accounts/messages/contacts/')
    .then(response => response.json())
    .then(data => {
        displayContacts(data.contacts);
    })
    .catch(error => {
        console.error('Error cargando contactos:', error);
    });
}

function formatTime(datetime) {
    const date = new Date(datetime);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    if (messageDate.getTime() === today.getTime()) {
        // Hoy - mostrar solo hora
        return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    } else if (messageDate.getTime() === today.getTime() - 86400000) {
        // Ayer
        return 'Ayer';
    } else if (date.getFullYear() === now.getFullYear()) {
        // Este año - mostrar fecha sin año
        return date.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' });
    } else {
        // Años anteriores - mostrar fecha completa
        return date.toLocaleDateString('es-ES');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Crear notificación toast
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remover el toast después de que se oculte
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Limpiar al salir de la página
window.addEventListener('beforeunload', function() {
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
    }
    if (typingTimeout) {
        clearTimeout(typingTimeout);
    }
});