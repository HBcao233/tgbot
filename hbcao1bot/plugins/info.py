from util import logger
from plugin import handler


@handler('info')
async def _(update, context, text=None):
  message = update.message
  
  def get_info(msg):
    logger.info(msg)
    info = []
    def get_chat_info(chat):
      name = chat.first_name or chat.title
      if getattr(chat, 'last_name', None):
        name += ' ' + chat.last_name
      info = [
        f'- name: <code>{name}</code>',
        f'- chat_id: <code>{chat.id}</code>',
      ]
      
      if getattr(chat, 'type', None):
        chat_type = chat.type
        if getattr(chat, 'is_bot', False):
          chat_type = 'bot'
        info.append(f'- type: {chat_type}')
      if getattr(chat, 'username', None):
        info.append(f'- username: <code>{chat.username}</code>')
      return '\n'.join(info)
    
    text = msg.text
    if getattr(msg, 'caption', None):
      text = msg.caption
    info = [
      f'message_id: <code>{msg.message_id}</code>',
      f'text: <code>{repr(text)}</code>',
      'chat: ',
      get_chat_info(msg.chat),
      'from_user: ',
      get_chat_info(msg.from_user),
    ]
    
    if getattr(msg, 'forward_origin', None):
      info.append(f'forward_origin: ',)
      if getattr(msg.forward_origin, 'sender_user', None):
        info.extend([
          get_chat_info(msg.forward_origin.sender_user),
          f'- type: {msg.forward_origin.type if not msg.forward_origin.sender_user.is_bot else "bot"}'
        ])
      elif getattr(msg.forward_origin, 'chat', None):
        info.append(get_chat_info(msg.forward_origin.chat))
      if getattr(msg.forward_origin, 'message_id', None):
        info.append(f'- message_id: <code>{msg.forward_origin.message_id}</code>')
    
    if getattr(msg, 'photo', None):
      info.extend([
        'photo: ', 
        f'- file_id: <code>{msg.photo[-1].file_id}</code>'
      ])
    if getattr(msg, 'video', None):
      info.extend([
        'video: ', 
        f'- file_id: <code>{msg.video.file_id}</code>'
      ])
    if getattr(msg, 'audio', None):
      info.extend([
        'audio: ', 
        f'- file_id: <code>{msg.audio.file_id}</code>'
      ])
    if getattr(msg, 'document', None):
      info.extend([
        'document: ', 
        f'- file_id: <code>{msg.document.file_id}</code>'
      ])
    if getattr(msg, 'sticker', None):
      info.extend([
        'sticker: ',
        f'- file_id: <code>{msg.sticker.file_id}</code>',
        f'- emoji: {msg.sticker.emoji}',
        f'- sticker_set: https://t.me/addstickers/{msg.sticker.set_name}',
      ])
    return '\n'.join(info)
  
  if getattr(message, 'reply_to_message', None):
    info = get_info(message.reply_to_message)
  else:
    info = get_info(message)
  await message.reply_text(
    info, quote=True,
    parse_mode='HTML',
  )
  