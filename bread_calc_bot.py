#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import logging
from decimal import Decimal, ROUND_UP
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler,
                          InlineQueryHandler, ConversationHandler, MessageHandler, Filters)
from datetime import datetime
import pytz

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

has_result = False

######################### Defs ##############################

# State definitions for descriptions conversation
CALCULATOR_SUBMENU, SELECTING_PARAMETER, TYPING, CALCULATOR, CALCULATE, CALCULATED = map(
    chr, range(7, 13))

# Meta states
GO_BACK, GO_BACK_CALCULATOR, BACK, CALCULATING, SAVE_INPUT, RESET = map(
    chr, range(14, 20))

# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Different constants
(DOUGH_WEIGHT, HYDRATION, SD_HYDRATION, STARTER, SALT, START_OVER, FEATURES,
 CURRENT_FEATURE, CURRENT_LEVEL) = map(chr, range(21, 30))

######################### Calculator #########################


def calculator_submenu(update, context,has_entered = False):
    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path, "users.log")
    log = open(path,"w")

    # print(context)
    # print("HERE CALC MENU")
    if(has_entered == False):
        dateTimeObj = datetime.now(pytz.timezone('Israel'))
        log.write("User started \n Username: {} with ID: {} Named: {} {} At {}".format(update.effective_user.username,
                                                                                       update.effective_user.id, update.effective_user.first_name, update.effective_user.last_name, dateTimeObj))
        has_entered = True

    global has_result
    ud = context.user_data
    #print ("Here Calc_Submenu")
    if not context.user_data.get(START_OVER):
        # context.user_data.clear()
        #print("HERE NOT GET STARTOVER")
        if(has_result == True):
            has_result = False
            ResultText = ud[FEATURES]["RESULT"]
            update.effective_message.reply_text(ResultText)
            if(update.callback_query):
                query = update.callback_query
                query.answer()
                query.edit_message_text(
                    text=calculator_submenu_message(),
                    reply_markup=calculator_submenu_keyboard())
            else:
                update.message.reply_text(
                    text=calculator_submenu_message(),
                    reply_markup=calculator_submenu_keyboard())
        else:
            #print("Here no result")
            context.user_data[FEATURES] = {DOUGH_WEIGHT: ""}
            if(update.callback_query):
                query = update.callback_query
                query.answer()
                query.edit_message_text(
                    text=calculator_submenu_message(),
                    reply_markup=calculator_submenu_keyboard())
            else:
                update.message.reply_text(
                    text=calculator_submenu_message(),
                    reply_markup=calculator_submenu_keyboard())
           
    # But after we do that, we need to send a new message
    else:
        #print("HERE GET STARTOVER")
        if(update.callback_query):
            query = update.callback_query
            query.answer()
            query.edit_message_text(
                text=calculator_submenu_message(),
                reply_markup=calculator_submenu_keyboard())
        else:
            update.message.reply_text(
                text=calculator_submenu_message(),
                reply_markup=calculator_submenu_keyboard())
        context.user_data[START_OVER] = False
    return CALCULATOR_SUBMENU


def param_switcher(param):

    if param == "DOUGH_WEIGHT":
        return('משקל בצק (בגרמים)')
    elif param == "HYDRATION":
        return ('אחוז הידרציה סופי (מספר בלבד)')
    elif param == "STARTER":
        return ('אחוז מחמצת (מספר בלבד)')
    elif param == "SALT":
        return ('אחוז מלח (מספר בלבד)')
    elif param == "SD_HYDRATION":
        return ('אחוז הידרציה במחמצת (מספר בלבד)')
    else:
        return ('ERR')


def ask_for_input(update, context):
    # Prompt user to input data for selected feature.
    # print("HERE_INPUT")
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        ask_for_input_message(update.callback_query.data))
    return SAVE_INPUT


def save_input(update, context):
    """Save input for feature and return to feature selection."""
    #print("HERE SAVE_INPUT")
    ud = context.user_data
    isDecimal = True
    curr_param = str(ud[CURRENT_FEATURE])
    try:
        curr_input = Decimal(update.message.text)
    except:
        isDecimal = False
    # print("isDecimal = {}".format(isDecimal))
    # print(curr_param)
    # print(curr_input)
    if(isDecimal == False or curr_input <= 0):
        context.bot.send_message(
            chat_id=update.message.chat_id, text=invalid_input_message())
        ud[START_OVER] = True
        return calculator_submenu(update, context,True)
    if(curr_param in ["HYDRATION","STARTER","SALT"]):
        if(curr_input > 100):
            context.bot.send_message(
                chat_id=update.message.chat_id, text=invalid_input_message())
            ud[START_OVER] = True
            return calculator_submenu(update, context,True)

    ud[FEATURES][ud[CURRENT_FEATURE]] = curr_input
    ud[START_OVER] = True
    return calculator_submenu(update, context,True)


def back_calc(update, context):
    """End conversation from InlineKeyboardButton."""
    # print("BACK")

    return CALCULATOR_SUBMENU


def invalid_input(update, context):
    update.reply_text(text=invalid_input_message())


def calculate(update, context):
    #print("HERE CALC")
    ud = context.user_data
    if not ud[FEATURES].get("DOUGH_WEIGHT") or not ud[FEATURES].get("HYDRATION") \
            or not ud[FEATURES].get("STARTER") or not ud[FEATURES].get("SALT") \
            or not ud[FEATURES].get("SD_HYDRATION"):
        # print("Here")
        query = update.callback_query
        query.answer()
        context.bot.send_message(chat_id=query.message.chat_id,text="נא ודא שמילאת את כל הפרמטרים.")
        ud[START_OVER] = True
        return calculator_submenu(update, context,True)

    Dough_Weight = float(ud[FEATURES]["DOUGH_WEIGHT"])
    Starter_Hydration = float(ud[FEATURES]["SD_HYDRATION"])/100
    Final_Hydration = float(ud[FEATURES]["HYDRATION"])/100
    Starter_Per = float(ud[FEATURES]["STARTER"])/100
    Salt_Per = float(ud[FEATURES]["SALT"])/100
    # #print(Starter_Per)
    Starter_Water_Per = Starter_Per/(1+(1/Starter_Hydration))
    Starter_Solid_Per = Starter_Per - Starter_Water_Per
    Water_Per = Final_Hydration * \
        (1 + Salt_Per + Starter_Solid_Per) - Starter_Water_Per
    Flour = Dough_Weight / (1 + Water_Per + Starter_Per + Salt_Per)
    Starter = Starter_Per * Flour
    Salt = Salt_Per * Flour
    Water = Water_Per * Flour
    # print("Starter hydrartion: {} , Final Hydration: {}".format(
    # Starter_Hydration, Final_Hydration))
    # print("Bread with total flour of {}g, {}g Water, {}g Starter, {}g Salt".format(
    # Flour, Water, Starter, Salt))
    calc_text = "קמח: {:.1f} גרם\n מים: {:.1f} גרם\n מחמצת: {:.1f} גרם\n מלח: {:.1f} גרם\n".format(
        Flour, Water, Starter, Salt)
    ud[FEATURES]["RESULT"] = calc_text
    # update.message.reply_text(text=calc_text)
    # #print(ud[FEATURES]["RESULT"])
    # update.callback_query.answer()
    ud[START_OVER] = False
    # #print(update.callback_query)
    dateTimeObj = datetime.now(pytz.timezone('Israel'))
    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path, "users.log")
    log = open(path,"w")
    log.write("User calculated:\n Username: {} with ID: {} Named: {} {} At {}".format(update.effective_user.username,
                                                                             update.effective_user.id, update.effective_user.first_name, update.effective_user.last_name, dateTimeObj))
    global has_result
    has_result = True
    return calculator_submenu(update, context,True)

######################### Keyboards ###############################


def calculator_submenu_keyboard():
    keyboard = [[InlineKeyboardButton("משקל בצק", callback_data="DOUGH_WEIGHT")],
                [InlineKeyboardButton(
                    "הידרציה סופית", callback_data="HYDRATION")],
                [InlineKeyboardButton("מחמצת", callback_data="STARTER")],
                [InlineKeyboardButton(
                    "הידרציית מחמצת", callback_data="SD_HYDRATION")],
                [InlineKeyboardButton("מלח", callback_data="SALT")],
                [InlineKeyboardButton("חשב", callback_data=str(CALCULATE))]]
    return InlineKeyboardMarkup(keyboard)

######################### Messages ###############################

# Error handler


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def calculator_submenu_message():
    return 'שלום, וברוך הבא למחשבון המחמצת העברי הראשון 🍞 \n נא הזן את הפרמטרים שלפניך ולאחר מכן לחץ "חשב".'


def ask_for_input_message(param):
    return 'נא הזן ' + param_switcher(param)


def invalid_input_message():
    return 'הקלט שהזנת אינו חוקי. נסה שנית.'

######################### Handlers ###############################


def main():

<<<<<<< HEAD
	TOKEN = None

	with open("token.txt") as f:
	    TOKEN = f.read().strip()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    #updater.dispatcher.add_handler(CallbackQueryHandler(ask_for_input, pattern='m2_1_1'))

    calculator_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', calculator_submenu)],
        states={
            CALCULATOR_SUBMENU: [
                CallbackQueryHandler(
                    ask_for_input, pattern='(DOUGH_WEIGHT|HYDRATION|STARTER|SALT|SD_HYDRATION)'),
                CallbackQueryHandler(
                    calculate, pattern='^' + str(CALCULATE) + '$')
                ],
            SAVE_INPUT: [
                MessageHandler(Filters.text, save_input)
            ]
        },
        fallbacks=[CommandHandler('start', calculator_submenu)],
        allow_reentry=True
    )

    # # log all errors
    # updater.dispatcher.add_handler(calculator_conv_handler)
    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(calculator_conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
