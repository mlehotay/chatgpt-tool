function getConversationMessages(conversation) {
    var messages = [];
    var currentNode = conversation.current_node;
    while (currentNode != null) {
        var node = conversation.mapping[currentNode];
        if (node.message &&
            node.message.content &&
            node.message.content.content_type == "text"
            && node.message.content.parts.length > 0 &&
            node.message.content.parts[0].length > 0 &&
            node.message.author.role != "system") {
            author = node.message.author.role;
            if (author === "assistant") {
                author = "ChatGPT";
            }
            messages.push({ author, text: node.message.content.parts[0] });
        }
        currentNode = node.parent;
    }
    return messages.reverse();
}

// on load, add messages to the root div
window.onload = function() {
    var root = document.getElementById("root");
    for (var i = 0; i < jsonData.length; i++) {
        var conversation = jsonData[i];
        var messages = getConversationMessages(conversation);
        var div = document.createElement("div");
        div.className = "conversation";
        div.innerHTML = "<h4>" + conversation.title + "</h4>";
        for (var j = 0; j < messages.length; j++) {
            var message = document.createElement("pre");
            message.className = "message";
            message.innerHTML = `<div class="author">${messages[j].author}</div><div>${messages[j].text}</div>`;
            div.appendChild(message);
        }
        root.appendChild(div);
    }
}
