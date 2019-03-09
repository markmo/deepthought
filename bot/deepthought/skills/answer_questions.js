const request = require('request');


module.exports = function(controller) {

    controller.hears('ask', 'message_received', function(bot, message) {
        request('http://dtapi:5000/ask?query=' + encodeURIComponent(message.text), function(err, resp, body) {
            // console.log(body);
            bot.reply(message, body);
        })
    })
};