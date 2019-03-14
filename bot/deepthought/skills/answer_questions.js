const request = require('request');


module.exports = function(controller) {

    controller.hears('ask', 'message_received', function(bot, message) {
        request('http://dtapi:5000/ask?query=' + encodeURIComponent(message.text), function(err, resp, body) {
            // console.log(body);
            bot.reply(message, body);
        })
    });

    controller.hears('alt_(.*)', 'message_received', function(bot, message) {
        const answer_num = parseInt(message.match[1]) - 1;
        controller.storage.users.get(message.user, function(err, user) {
            const answers = user.answers;
            const n_answers = answers.length;
            let quick_replies = [];
            for (let i = 0; i < n_answers; i++) {
                if (i === answer_num) {
                    continue
                }
                quick_replies.push({
                    title: 'Alt ' + (i + 1),
                    payload: 'alt_' + (i + 1)
                })
            }
            const reply = {
                text: answers[answer_num][1],
                quick_replies: quick_replies
            };
            bot.reply(message, reply);
        });
    });

    controller.hears('tell', 'message_received', function(bot, message) {
        request('http://dtapi:5000/ask4?query=' + encodeURIComponent(message.text), function(err, resp, body) {
            body = JSON.parse(body);
            const n_answers = body.length;
            let quick_replies = [];
            for (let i = 1; i < n_answers; i++) {
                quick_replies.push({
                    title: 'Alt ' + (i + 1),
                    payload: 'alt_' + (i + 1)
                })
            }
            const reply = {
                text: body[0][1],
                quick_replies: quick_replies
            };
            controller.storage.users.save({id: message.user, answers: body});
            bot.reply(message, reply);
        })
    });

    controller.hears(['explore', 'exp'], 'message_received', function(bot, message) {
        request('http://dtapi:5000/ask?query=' + encodeURIComponent(message.text), function(err, resp, body) {
            const response = body;
            request('http://dtapi:5000/topics?query=' + encodeURIComponent(message.text), function(err, resp, body) {
                body = JSON.parse(body);
                const n_topics = body.length;
                let quick_replies = [];
                for (let i = 0; i < n_topics; i++) {
                    quick_replies.push({
                        title: body[i],
                        payload: 'exp ' + body[i]
                    })
                }
                const reply = {
                    text: response,
                    quick_replies: quick_replies
                };
                bot.reply(message, reply);
            })
        })
    })
};