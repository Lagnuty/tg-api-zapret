# Implemented MTProto Layer 1 Functions

Source: `docs/mtproto-importance-layers.json`.
Layer: `1`.
Implemented functions: `248` / `248`.

All Layer 1 request-functions are implemented through the dynamic MTProto layer dispatcher. Individual functions are executed by callable_path with kwargs.

## Endpoints

- `GET /mtproto/layers/1/functions`
- `POST /mtproto/layers/1/invoke`
- `POST /raw/invoke`
- `POST /rpc` with `method=raw.invoke`

## Functions

| Implemented | Namespace | Function | Callable Path | Signature |
|---|---|---|---|---|
| `True` | `account` | `AcceptAuthorizationRequest` | `account.AcceptAuthorizationRequest` | `(self, bot_id: int, scope: str, public_key: str, value_hashes: List[ForwardRef('TypeSecureValueHash')], credentials: 'TypeSecureCredentialsEncrypted')` |
| `True` | `account` | `ChangeAuthorizationSettingsRequest` | `account.ChangeAuthorizationSettingsRequest` | `(self, hash: int, confirmed: Optional[bool] = None, encrypted_requests_disabled: Optional[bool] = None, call_requests_disabled: Optional[bool] = None)` |
| `True` | `account` | `CheckUsernameRequest` | `account.CheckUsernameRequest` | `(self, username: str)` |
| `True` | `account` | `CreateBusinessChatLinkRequest` | `account.CreateBusinessChatLinkRequest` | `(self, link: 'TypeInputBusinessChatLink')` |
| `True` | `account` | `DeleteBusinessChatLinkRequest` | `account.DeleteBusinessChatLinkRequest` | `(self, slug: str)` |
| `True` | `account` | `DisablePeerConnectedBotRequest` | `account.DisablePeerConnectedBotRequest` | `(self, peer: 'TypeInputPeer')` |
| `True` | `account` | `EditBusinessChatLinkRequest` | `account.EditBusinessChatLinkRequest` | `(self, slug: str, link: 'TypeInputBusinessChatLink')` |
| `True` | `account` | `GetAuthorizationFormRequest` | `account.GetAuthorizationFormRequest` | `(self, bot_id: int, scope: str, public_key: str)` |
| `True` | `account` | `GetAuthorizationsRequest` | `account.GetAuthorizationsRequest` | `(self, /, *args, **kwargs)` |
| `True` | `account` | `GetBusinessChatLinksRequest` | `account.GetBusinessChatLinksRequest` | `(self, /, *args, **kwargs)` |
| `True` | `account` | `GetChannelDefaultEmojiStatusesRequest` | `account.GetChannelDefaultEmojiStatusesRequest` | `(self, hash: int)` |
| `True` | `account` | `GetChannelRestrictedStatusEmojisRequest` | `account.GetChannelRestrictedStatusEmojisRequest` | `(self, hash: int)` |
| `True` | `account` | `GetChatThemesRequest` | `account.GetChatThemesRequest` | `(self, hash: int)` |
| `True` | `account` | `GetPaidMessagesRevenueRequest` | `account.GetPaidMessagesRevenueRequest` | `(self, user_id: 'TypeInputUser', parent_peer: Optional[ForwardRef('TypeInputPeer')] = None)` |
| `True` | `account` | `GetUniqueGiftChatThemesRequest` | `account.GetUniqueGiftChatThemesRequest` | `(self, offset: str, limit: int, hash: int)` |
| `True` | `account` | `GetWebAuthorizationsRequest` | `account.GetWebAuthorizationsRequest` | `(self, /, *args, **kwargs)` |
| `True` | `account` | `ReorderUsernamesRequest` | `account.ReorderUsernamesRequest` | `(self, order: List[str])` |
| `True` | `account` | `ReportPeerRequest` | `account.ReportPeerRequest` | `(self, peer: 'TypeInputPeer', reason: 'TypeReportReason', message: str)` |
| `True` | `account` | `ResetAuthorizationRequest` | `account.ResetAuthorizationRequest` | `(self, hash: int)` |
| `True` | `account` | `ResetWebAuthorizationRequest` | `account.ResetWebAuthorizationRequest` | `(self, hash: int)` |
| `True` | `account` | `ResetWebAuthorizationsRequest` | `account.ResetWebAuthorizationsRequest` | `(self, /, *args, **kwargs)` |
| `True` | `account` | `ResolveBusinessChatLinkRequest` | `account.ResolveBusinessChatLinkRequest` | `(self, slug: str)` |
| `True` | `account` | `SetAuthorizationTTLRequest` | `account.SetAuthorizationTTLRequest` | `(self, authorization_ttl_days: int)` |
| `True` | `account` | `ToggleNoPaidMessagesExceptionRequest` | `account.ToggleNoPaidMessagesExceptionRequest` | `(self, user_id: 'TypeInputUser', refund_charged: Optional[bool] = None, require_payment: Optional[bool] = None, parent_peer: Optional[ForwardRef('TypeInputPeer')] = None)` |
| `True` | `account` | `ToggleSponsoredMessagesRequest` | `account.ToggleSponsoredMessagesRequest` | `(self, enabled: bool)` |
| `True` | `account` | `ToggleUsernameRequest` | `account.ToggleUsernameRequest` | `(self, username: str, active: bool)` |
| `True` | `account` | `UpdateBirthdayRequest` | `account.UpdateBirthdayRequest` | `(self, birthday: Optional[ForwardRef('TypeBirthday')] = None)` |
| `True` | `account` | `UpdateBusinessAwayMessageRequest` | `account.UpdateBusinessAwayMessageRequest` | `(self, message: Optional[ForwardRef('TypeInputBusinessAwayMessage')] = None)` |
| `True` | `account` | `UpdateBusinessGreetingMessageRequest` | `account.UpdateBusinessGreetingMessageRequest` | `(self, message: Optional[ForwardRef('TypeInputBusinessGreetingMessage')] = None)` |
| `True` | `account` | `UpdateBusinessIntroRequest` | `account.UpdateBusinessIntroRequest` | `(self, intro: Optional[ForwardRef('TypeInputBusinessIntro')] = None)` |
| `True` | `account` | `UpdateBusinessLocationRequest` | `account.UpdateBusinessLocationRequest` | `(self, geo_point: Optional[ForwardRef('TypeInputGeoPoint')] = None, address: Optional[str] = None)` |
| `True` | `account` | `UpdateBusinessWorkHoursRequest` | `account.UpdateBusinessWorkHoursRequest` | `(self, business_work_hours: Optional[ForwardRef('TypeBusinessWorkHours')] = None)` |
| `True` | `account` | `UpdateColorRequest` | `account.UpdateColorRequest` | `(self, for_profile: Optional[bool] = None, color: Optional[ForwardRef('TypePeerColor')] = None)` |
| `True` | `account` | `UpdateConnectedBotRequest` | `account.UpdateConnectedBotRequest` | `(self, bot: 'TypeInputUser', recipients: 'TypeInputBusinessBotRecipients', deleted: Optional[bool] = None, rights: Optional[ForwardRef('TypeBusinessBotRights')] = None)` |
| `True` | `account` | `UpdateDeviceLockedRequest` | `account.UpdateDeviceLockedRequest` | `(self, period: int)` |
| `True` | `account` | `UpdateEmojiStatusRequest` | `account.UpdateEmojiStatusRequest` | `(self, emoji_status: 'TypeEmojiStatus')` |
| `True` | `account` | `UpdateNotifySettingsRequest` | `account.UpdateNotifySettingsRequest` | `(self, peer: 'TypeInputNotifyPeer', settings: 'TypeInputPeerNotifySettings')` |
| `True` | `account` | `UpdatePasswordSettingsRequest` | `account.UpdatePasswordSettingsRequest` | `(self, password: 'TypeInputCheckPasswordSRP', new_settings: 'TypePasswordInputSettings')` |
| `True` | `account` | `UpdatePersonalChannelRequest` | `account.UpdatePersonalChannelRequest` | `(self, channel: 'TypeInputChannel')` |
| `True` | `account` | `UpdateProfileRequest` | `account.UpdateProfileRequest` | `(self, first_name: Optional[str] = None, last_name: Optional[str] = None, about: Optional[str] = None)` |
| `True` | `account` | `UpdateStatusRequest` | `account.UpdateStatusRequest` | `(self, offline: bool)` |
| `True` | `account` | `UpdateThemeRequest` | `account.UpdateThemeRequest` | `(self, format: str, theme: 'TypeInputTheme', slug: Optional[str] = None, title: Optional[str] = None, document: Optional[ForwardRef('TypeInputDocument')] = None, settings: Optional[List[ForwardRef('TypeInputThemeSettings')]] = None)` |
| `True` | `account` | `UpdateUsernameRequest` | `account.UpdateUsernameRequest` | `(self, username: str)` |
| `True` | `account` | `UpdateWebBrowserSettingsRequest` | `account.UpdateWebBrowserSettingsRequest` | `(self, open_external_browser: Optional[bool] = None, display_close_button: Optional[bool] = None)` |
| `True` | `aicompose` | `UpdateToneRequest` | `aicompose.UpdateToneRequest` | `(self, tone: 'TypeInputAiComposeTone', display_author: Optional[bool] = None, emoji_id: Optional[int] = None, title: Optional[str] = None, prompt: Optional[str] = None)` |
| `True` | `auth` | `AcceptLoginTokenRequest` | `auth.AcceptLoginTokenRequest` | `(self, token: bytes)` |
| `True` | `auth` | `BindTempAuthKeyRequest` | `auth.BindTempAuthKeyRequest` | `(self, perm_auth_key_id: int, nonce: int, expires_at: Optional[datetime.datetime], encrypted_message: bytes)` |
| `True` | `auth` | `CancelCodeRequest` | `auth.CancelCodeRequest` | `(self, phone_number: str, phone_code_hash: str)` |
| `True` | `auth` | `CheckPaidAuthRequest` | `auth.CheckPaidAuthRequest` | `(self, phone_number: str, phone_code_hash: str, form_id: int)` |
| `True` | `auth` | `CheckPasswordRequest` | `auth.CheckPasswordRequest` | `(self, password: 'TypeInputCheckPasswordSRP')` |
| `True` | `auth` | `CheckRecoveryPasswordRequest` | `auth.CheckRecoveryPasswordRequest` | `(self, code: str)` |
| `True` | `auth` | `DropTempAuthKeysRequest` | `auth.DropTempAuthKeysRequest` | `(self, except_auth_keys: List[int])` |
| `True` | `auth` | `ExportAuthorizationRequest` | `auth.ExportAuthorizationRequest` | `(self, dc_id: int)` |
| `True` | `auth` | `ExportLoginTokenRequest` | `auth.ExportLoginTokenRequest` | `(self, api_id: int, api_hash: str, except_ids: List[int])` |
| `True` | `auth` | `FinishPasskeyLoginRequest` | `auth.FinishPasskeyLoginRequest` | `(self, credential: 'TypeInputPasskeyCredential', from_dc_id: Optional[int] = None, from_auth_key_id: Optional[int] = None)` |
| `True` | `auth` | `ImportAuthorizationRequest` | `auth.ImportAuthorizationRequest` | `(self, id: int, bytes: bytes)` |
| `True` | `auth` | `ImportBotAuthorizationRequest` | `auth.ImportBotAuthorizationRequest` | `(self, flags: int, api_id: int, api_hash: str, bot_auth_token: str)` |
| `True` | `auth` | `ImportLoginTokenRequest` | `auth.ImportLoginTokenRequest` | `(self, token: bytes)` |
| `True` | `auth` | `ImportWebTokenAuthorizationRequest` | `auth.ImportWebTokenAuthorizationRequest` | `(self, api_id: int, api_hash: str, web_auth_token: str)` |
| `True` | `auth` | `InitPasskeyLoginRequest` | `auth.InitPasskeyLoginRequest` | `(self, api_id: int, api_hash: str)` |
| `True` | `auth` | `LogOutRequest` | `auth.LogOutRequest` | `(self, /, *args, **kwargs)` |
| `True` | `auth` | `RecoverPasswordRequest` | `auth.RecoverPasswordRequest` | `(self, code: str, new_settings: Optional[ForwardRef('TypePasswordInputSettings')] = None)` |
| `True` | `auth` | `ReportMissingCodeRequest` | `auth.ReportMissingCodeRequest` | `(self, phone_number: str, phone_code_hash: str, mnc: str)` |
| `True` | `auth` | `RequestFirebaseSmsRequest` | `auth.RequestFirebaseSmsRequest` | `(self, phone_number: str, phone_code_hash: str, safety_net_token: Optional[str] = None, play_integrity_token: Optional[str] = None, ios_push_secret: Optional[str] = None)` |
| `True` | `auth` | `RequestPasswordRecoveryRequest` | `auth.RequestPasswordRecoveryRequest` | `(self, /, *args, **kwargs)` |
| `True` | `auth` | `ResendCodeRequest` | `auth.ResendCodeRequest` | `(self, phone_number: str, phone_code_hash: str, reason: Optional[str] = None)` |
| `True` | `auth` | `ResetAuthorizationsRequest` | `auth.ResetAuthorizationsRequest` | `(self, /, *args, **kwargs)` |
| `True` | `auth` | `ResetLoginEmailRequest` | `auth.ResetLoginEmailRequest` | `(self, phone_number: str, phone_code_hash: str)` |
| `True` | `auth` | `SendCodeRequest` | `auth.SendCodeRequest` | `(self, phone_number: str, api_id: int, api_hash: str, settings: 'TypeCodeSettings')` |
| `True` | `auth` | `SignInRequest` | `auth.SignInRequest` | `(self, phone_number: str, phone_code_hash: str, phone_code: Optional[str] = None, email_verification: Optional[ForwardRef('TypeEmailVerification')] = None)` |
| `True` | `auth` | `SignUpRequest` | `auth.SignUpRequest` | `(self, phone_number: str, phone_code_hash: str, first_name: str, last_name: str, no_joined_notifications: Optional[bool] = None)` |
| `True` | `bots` | `AllowSendMessageRequest` | `bots.AllowSendMessageRequest` | `(self, bot: 'TypeInputUser')` |
| `True` | `bots` | `CanSendMessageRequest` | `bots.CanSendMessageRequest` | `(self, bot: 'TypeInputUser')` |
| `True` | `bots` | `CheckUsernameRequest` | `bots.CheckUsernameRequest` | `(self, username: str)` |
| `True` | `bots` | `ReorderUsernamesRequest` | `bots.ReorderUsernamesRequest` | `(self, bot: 'TypeInputUser', order: List[str])` |
| `True` | `bots` | `SetJoinChatResultsRequest` | `bots.SetJoinChatResultsRequest` | `(self, query_id: int, result: 'TypeJoinChatBotResult')` |
| `True` | `bots` | `ToggleUserEmojiStatusPermissionRequest` | `bots.ToggleUserEmojiStatusPermissionRequest` | `(self, bot: 'TypeInputUser', enabled: bool)` |
| `True` | `bots` | `ToggleUsernameRequest` | `bots.ToggleUsernameRequest` | `(self, bot: 'TypeInputUser', username: str, active: bool)` |
| `True` | `bots` | `UpdateStarRefProgramRequest` | `bots.UpdateStarRefProgramRequest` | `(self, bot: 'TypeInputUser', commission_permille: int, duration_months: Optional[int] = None)` |
| `True` | `bots` | `UpdateUserEmojiStatusRequest` | `bots.UpdateUserEmojiStatusRequest` | `(self, user_id: 'TypeInputUser', emoji_status: 'TypeEmojiStatus')` |
| `True` | `channels` | `CheckUsernameRequest` | `channels.CheckUsernameRequest` | `(self, channel: 'TypeInputChannel', username: str)` |
| `True` | `channels` | `CreateChannelRequest` | `channels.CreateChannelRequest` | `(self, title: str, about: str, broadcast: Optional[bool] = None, megagroup: Optional[bool] = None, for_import: Optional[bool] = None, forum: Optional[bool] = None, geo_point: Optional[ForwardRef('TypeInputGeoPoint')] = None, address: Optional[str] = None, ttl_period: Optional[int] = None)` |
| `True` | `channels` | `DeactivateAllUsernamesRequest` | `channels.DeactivateAllUsernamesRequest` | `(self, channel: 'TypeInputChannel')` |
| `True` | `channels` | `DeleteChannelRequest` | `channels.DeleteChannelRequest` | `(self, channel: 'TypeInputChannel')` |
| `True` | `channels` | `DeleteMessagesRequest` | `channels.DeleteMessagesRequest` | `(self, channel: 'TypeInputChannel', id: List[int])` |
| `True` | `channels` | `ExportMessageLinkRequest` | `channels.ExportMessageLinkRequest` | `(self, channel: 'TypeInputChannel', id: int, grouped: Optional[bool] = None, thread: Optional[bool] = None)` |
| `True` | `channels` | `GetAdminedPublicChannelsRequest` | `channels.GetAdminedPublicChannelsRequest` | `(self, by_location: Optional[bool] = None, check_limit: Optional[bool] = None, for_personal: Optional[bool] = None)` |
| `True` | `channels` | `GetChannelRecommendationsRequest` | `channels.GetChannelRecommendationsRequest` | `(self, channel: Optional[ForwardRef('TypeInputChannel')] = None)` |
| `True` | `channels` | `GetChannelsRequest` | `channels.GetChannelsRequest` | `(self, id: List[ForwardRef('TypeInputChannel')])` |
| `True` | `channels` | `GetFullChannelRequest` | `channels.GetFullChannelRequest` | `(self, channel: 'TypeInputChannel')` |
| `True` | `channels` | `GetInactiveChannelsRequest` | `channels.GetInactiveChannelsRequest` | `(self, /, *args, **kwargs)` |
| `True` | `channels` | `GetLeftChannelsRequest` | `channels.GetLeftChannelsRequest` | `(self, offset: int)` |
| `True` | `channels` | `GetMessageAuthorRequest` | `channels.GetMessageAuthorRequest` | `(self, channel: 'TypeInputChannel', id: int)` |
| `True` | `channels` | `GetMessagesRequest` | `channels.GetMessagesRequest` | `(self, channel: 'TypeInputChannel', id: List[ForwardRef('TypeInputMessage')])` |
| `True` | `channels` | `InviteToChannelRequest` | `channels.InviteToChannelRequest` | `(self, channel: 'TypeInputChannel', users: List[ForwardRef('TypeInputUser')])` |
| `True` | `channels` | `JoinChannelRequest` | `channels.JoinChannelRequest` | `(self, channel: 'TypeInputChannel')` |
| `True` | `channels` | `LeaveChannelRequest` | `channels.LeaveChannelRequest` | `(self, channel: 'TypeInputChannel')` |
| `True` | `channels` | `ReadMessageContentsRequest` | `channels.ReadMessageContentsRequest` | `(self, channel: 'TypeInputChannel', id: List[int])` |
| `True` | `channels` | `ReorderUsernamesRequest` | `channels.ReorderUsernamesRequest` | `(self, channel: 'TypeInputChannel', order: List[str])` |
| `True` | `channels` | `RestrictSponsoredMessagesRequest` | `channels.RestrictSponsoredMessagesRequest` | `(self, channel: 'TypeInputChannel', restricted: bool)` |
| `True` | `channels` | `ToggleUsernameRequest` | `channels.ToggleUsernameRequest` | `(self, channel: 'TypeInputChannel', username: str, active: bool)` |
| `True` | `channels` | `ToggleViewForumAsMessagesRequest` | `channels.ToggleViewForumAsMessagesRequest` | `(self, channel: 'TypeInputChannel', enabled: bool)` |
| `True` | `channels` | `UpdateColorRequest` | `channels.UpdateColorRequest` | `(self, channel: 'TypeInputChannel', for_profile: Optional[bool] = None, color: Optional[int] = None, background_emoji_id: Optional[int] = None)` |
| `True` | `channels` | `UpdateEmojiStatusRequest` | `channels.UpdateEmojiStatusRequest` | `(self, channel: 'TypeInputChannel', emoji_status: 'TypeEmojiStatus')` |
| `True` | `channels` | `UpdatePaidMessagesPriceRequest` | `channels.UpdatePaidMessagesPriceRequest` | `(self, channel: 'TypeInputChannel', send_paid_messages_stars: int, broadcast_messages_allowed: Optional[bool] = None)` |
| `True` | `channels` | `UpdateUsernameRequest` | `channels.UpdateUsernameRequest` | `(self, channel: 'TypeInputChannel', username: str)` |
| `True` | `chatlists` | `CheckChatlistInviteRequest` | `chatlists.CheckChatlistInviteRequest` | `(self, slug: str)` |
| `True` | `chatlists` | `ExportChatlistInviteRequest` | `chatlists.ExportChatlistInviteRequest` | `(self, chatlist: 'TypeInputChatlist', title: str, peers: List[ForwardRef('TypeInputPeer')])` |
| `True` | `chatlists` | `GetChatlistUpdatesRequest` | `chatlists.GetChatlistUpdatesRequest` | `(self, chatlist: 'TypeInputChatlist')` |
| `True` | `chatlists` | `GetLeaveChatlistSuggestionsRequest` | `chatlists.GetLeaveChatlistSuggestionsRequest` | `(self, chatlist: 'TypeInputChatlist')` |
| `True` | `chatlists` | `HideChatlistUpdatesRequest` | `chatlists.HideChatlistUpdatesRequest` | `(self, chatlist: 'TypeInputChatlist')` |
| `True` | `chatlists` | `JoinChatlistInviteRequest` | `chatlists.JoinChatlistInviteRequest` | `(self, slug: str, peers: List[ForwardRef('TypeInputPeer')])` |
| `True` | `chatlists` | `JoinChatlistUpdatesRequest` | `chatlists.JoinChatlistUpdatesRequest` | `(self, chatlist: 'TypeInputChatlist', peers: List[ForwardRef('TypeInputPeer')])` |
| `True` | `chatlists` | `LeaveChatlistRequest` | `chatlists.LeaveChatlistRequest` | `(self, chatlist: 'TypeInputChatlist', peers: List[ForwardRef('TypeInputPeer')])` |
| `True` | `contacts` | `GetSponsoredPeersRequest` | `contacts.GetSponsoredPeersRequest` | `(self, q: str)` |
| `True` | `contacts` | `GetTopPeersRequest` | `contacts.GetTopPeersRequest` | `(self, offset: int, limit: int, hash: int, correspondents: Optional[bool] = None, bots_pm: Optional[bool] = None, bots_inline: Optional[bool] = None, phone_calls: Optional[bool] = None, forward_users: Optional[bool] = None, forward_chats: Optional[bool] = None, groups: Optional[bool] = None, channels: Optional[bool] = None, bots_app: Optional[bool] = None, bots_guestchat: Optional[bool] = None)` |
| `True` | `contacts` | `ResetTopPeerRatingRequest` | `contacts.ResetTopPeerRatingRequest` | `(self, category: 'TypeTopPeerCategory', peer: 'TypeInputPeer')` |
| `True` | `contacts` | `ResolveUsernameRequest` | `contacts.ResolveUsernameRequest` | `(self, username: str, referer: Optional[str] = None)` |
| `True` | `contacts` | `ToggleTopPeersRequest` | `contacts.ToggleTopPeersRequest` | `(self, enabled: bool)` |
| `True` | `contacts` | `UpdateContactNoteRequest` | `contacts.UpdateContactNoteRequest` | `(self, id: 'TypeInputUser', note: 'TypeTextWithEntities')` |
| `True` | `folders` | `EditPeerFoldersRequest` | `folders.EditPeerFoldersRequest` | `(self, folder_peers: List[ForwardRef('TypeInputFolderPeer')])` |
| `True` | `help` | `EditUserInfoRequest` | `help.EditUserInfoRequest` | `(self, user_id: 'TypeInputUser', message: str, entities: List[ForwardRef('TypeMessageEntity')])` |
| `True` | `help` | `GetAppUpdateRequest` | `help.GetAppUpdateRequest` | `(self, source: str)` |
| `True` | `help` | `GetPeerColorsRequest` | `help.GetPeerColorsRequest` | `(self, hash: int)` |
| `True` | `help` | `GetPeerProfileColorsRequest` | `help.GetPeerProfileColorsRequest` | `(self, hash: int)` |
| `True` | `help` | `GetTermsOfServiceUpdateRequest` | `help.GetTermsOfServiceUpdateRequest` | `(self, /, *args, **kwargs)` |
| `True` | `help` | `GetUserInfoRequest` | `help.GetUserInfoRequest` | `(self, user_id: 'TypeInputUser')` |
| `True` | `help` | `SetBotUpdatesStatusRequest` | `help.SetBotUpdatesStatusRequest` | `(self, pending_updates_count: int, message: str)` |
| `True` | `messages` | `AddChatUserRequest` | `messages.AddChatUserRequest` | `(self, chat_id: int, user_id: 'TypeInputUser', fwd_limit: int)` |
| `True` | `messages` | `CheckChatInviteRequest` | `messages.CheckChatInviteRequest` | `(self, hash: str)` |
| `True` | `messages` | `CheckHistoryImportPeerRequest` | `messages.CheckHistoryImportPeerRequest` | `(self, peer: 'TypeInputPeer')` |
| `True` | `messages` | `ClickSponsoredMessageRequest` | `messages.ClickSponsoredMessageRequest` | `(self, media: Optional[bool] = None, fullscreen: Optional[bool] = None, random_id: bytes = None)` |
| `True` | `messages` | `ComposeMessageWithAIRequest` | `messages.ComposeMessageWithAIRequest` | `(self, text: 'TypeTextWithEntities', proofread: Optional[bool] = None, emojify: Optional[bool] = None, translate_to_lang: Optional[str] = None, tone: Optional[ForwardRef('TypeInputAiComposeTone')] = None)` |
| `True` | `messages` | `CreateChatRequest` | `messages.CreateChatRequest` | `(self, users: List[ForwardRef('TypeInputUser')], title: str, ttl_period: Optional[int] = None)` |
| `True` | `messages` | `DeleteChatRequest` | `messages.DeleteChatRequest` | `(self, chat_id: int)` |
| `True` | `messages` | `DeleteChatUserRequest` | `messages.DeleteChatUserRequest` | `(self, chat_id: int, user_id: 'TypeInputUser', revoke_history: Optional[bool] = None)` |
| `True` | `messages` | `DeleteExportedChatInviteRequest` | `messages.DeleteExportedChatInviteRequest` | `(self, peer: 'TypeInputPeer', link: str)` |
| `True` | `messages` | `DeleteMessagesRequest` | `messages.DeleteMessagesRequest` | `(self, id: List[int], revoke: Optional[bool] = None)` |
| `True` | `messages` | `DeleteQuickReplyMessagesRequest` | `messages.DeleteQuickReplyMessagesRequest` | `(self, shortcut_id: int, id: List[int])` |
| `True` | `messages` | `DeleteRevokedExportedChatInvitesRequest` | `messages.DeleteRevokedExportedChatInvitesRequest` | `(self, peer: 'TypeInputPeer', admin_id: 'TypeInputUser')` |
| `True` | `messages` | `DeleteScheduledMessagesRequest` | `messages.DeleteScheduledMessagesRequest` | `(self, peer: 'TypeInputPeer', id: List[int])` |
| `True` | `messages` | `EditChatAboutRequest` | `messages.EditChatAboutRequest` | `(self, peer: 'TypeInputPeer', about: str)` |
| `True` | `messages` | `EditChatAdminRequest` | `messages.EditChatAdminRequest` | `(self, chat_id: int, user_id: 'TypeInputUser', is_admin: bool)` |
| `True` | `messages` | `EditChatCreatorRequest` | `messages.EditChatCreatorRequest` | `(self, peer: 'TypeInputPeer', user_id: 'TypeInputUser', password: 'TypeInputCheckPasswordSRP')` |
| `True` | `messages` | `EditChatDefaultBannedRightsRequest` | `messages.EditChatDefaultBannedRightsRequest` | `(self, peer: 'TypeInputPeer', banned_rights: 'TypeChatBannedRights')` |
| `True` | `messages` | `EditChatParticipantRankRequest` | `messages.EditChatParticipantRankRequest` | `(self, peer: 'TypeInputPeer', participant: 'TypeInputPeer', rank: str)` |
| `True` | `messages` | `EditChatPhotoRequest` | `messages.EditChatPhotoRequest` | `(self, chat_id: int, photo: 'TypeInputChatPhoto')` |
| `True` | `messages` | `EditChatTitleRequest` | `messages.EditChatTitleRequest` | `(self, chat_id: int, title: str)` |
| `True` | `messages` | `EditExportedChatInviteRequest` | `messages.EditExportedChatInviteRequest` | `(self, peer: 'TypeInputPeer', link: str, revoked: Optional[bool] = None, expire_date: Optional[datetime.datetime] = None, usage_limit: Optional[int] = None, request_needed: Optional[bool] = None, title: Optional[str] = None)` |
| `True` | `messages` | `EditInlineBotMessageRequest` | `messages.EditInlineBotMessageRequest` | `(self, id: 'TypeInputBotInlineMessageID', no_webpage: Optional[bool] = None, invert_media: Optional[bool] = None, message: Optional[str] = None, media: Optional[ForwardRef('TypeInputMedia')] = None, reply_markup: Optional[ForwardRef('TypeReplyMarkup')] = None, entities: Optional[List[ForwardRef('TypeMessageEntity')]] = None, rich_message: Optional[ForwardRef('TypeInputRichMessage')] = None)` |
| `True` | `messages` | `EditMessageRequest` | `messages.EditMessageRequest` | `(self, peer: 'TypeInputPeer', id: int, no_webpage: Optional[bool] = None, invert_media: Optional[bool] = None, message: Optional[str] = None, media: Optional[ForwardRef('TypeInputMedia')] = None, reply_markup: Optional[ForwardRef('TypeReplyMarkup')] = None, entities: Optional[List[ForwardRef('TypeMessageEntity')]] = None, schedule_date: Optional[datetime.datetime] = None, schedule_repeat_period: Optional[int] = None, quick_reply_shortcut_id: Optional[int] = None, rich_message: Optional[ForwardRef('TypeInputRichMessage')] = None)` |
| `True` | `messages` | `ExportChatInviteRequest` | `messages.ExportChatInviteRequest` | `(self, peer: 'TypeInputPeer', legacy_revoke_permanent: Optional[bool] = None, request_needed: Optional[bool] = None, expire_date: Optional[datetime.datetime] = None, usage_limit: Optional[int] = None, title: Optional[str] = None, subscription_pricing: Optional[ForwardRef('TypeStarsSubscriptionPricing')] = None)` |
| `True` | `messages` | `ForwardMessagesRequest` | `messages.ForwardMessagesRequest` | `(self, from_peer: 'TypeInputPeer', id: List[int], to_peer: 'TypeInputPeer', silent: Optional[bool] = None, background: Optional[bool] = None, with_my_score: Optional[bool] = None, drop_author: Optional[bool] = None, drop_media_captions: Optional[bool] = None, noforwards: Optional[bool] = None, allow_paid_floodskip: Optional[bool] = None, random_id: List[int] = None, top_msg_id: Optional[int] = None, reply_to: Optional[ForwardRef('TypeInputReplyTo')] = None, schedule_date: Optional[datetime.datetime] = None, schedule_repeat_period: Optional[int] = None, send_as: Optional[ForwardRef('TypeInputPeer')] = None, quick_reply_shortcut: Optional[ForwardRef('TypeInputQuickReplyShortcut')] = None, effect: Optional[int] = None, video_timestamp: Optional[int] = None, allow_paid_stars: Optional[int] = None, suggested_post: Optional[ForwardRef('TypeSuggestedPost')] = None)` |
| `True` | `messages` | `GetChatInviteImportersRequest` | `messages.GetChatInviteImportersRequest` | `(self, peer: 'TypeInputPeer', offset_date: Optional[datetime.datetime], offset_user: 'TypeInputUser', limit: int, requested: Optional[bool] = None, subscription_expired: Optional[bool] = None, link: Optional[str] = None, q: Optional[str] = None)` |
| `True` | `messages` | `GetChatsRequest` | `messages.GetChatsRequest` | `(self, id: List[int])` |
| `True` | `messages` | `GetCommonChatsRequest` | `messages.GetCommonChatsRequest` | `(self, user_id: 'TypeInputUser', max_id: int, limit: int)` |
| `True` | `messages` | `GetDialogFiltersRequest` | `messages.GetDialogFiltersRequest` | `(self, /, *args, **kwargs)` |
| `True` | `messages` | `GetDialogUnreadMarksRequest` | `messages.GetDialogUnreadMarksRequest` | `(self, parent_peer: Optional[ForwardRef('TypeInputPeer')] = None)` |
| `True` | `messages` | `GetDialogsRequest` | `messages.GetDialogsRequest` | `(self, offset_date: Optional[datetime.datetime], offset_id: int, offset_peer: 'TypeInputPeer', limit: int, hash: int, exclude_pinned: Optional[bool] = None, folder_id: Optional[int] = None)` |
| `True` | `messages` | `GetDiscussionMessageRequest` | `messages.GetDiscussionMessageRequest` | `(self, peer: 'TypeInputPeer', msg_id: int)` |
| `True` | `messages` | `GetExportedChatInviteRequest` | `messages.GetExportedChatInviteRequest` | `(self, peer: 'TypeInputPeer', link: str)` |
| `True` | `messages` | `GetExportedChatInvitesRequest` | `messages.GetExportedChatInvitesRequest` | `(self, peer: 'TypeInputPeer', admin_id: 'TypeInputUser', limit: int, revoked: Optional[bool] = None, offset_date: Optional[datetime.datetime] = None, offset_link: Optional[str] = None)` |
| `True` | `messages` | `GetFullChatRequest` | `messages.GetFullChatRequest` | `(self, chat_id: int)` |
| `True` | `messages` | `GetFutureChatCreatorAfterLeaveRequest` | `messages.GetFutureChatCreatorAfterLeaveRequest` | `(self, peer: 'TypeInputPeer')` |
| `True` | `messages` | `GetHistoryRequest` | `messages.GetHistoryRequest` | `(self, peer: 'TypeInputPeer', offset_id: int, offset_date: Optional[datetime.datetime], add_offset: int, limit: int, max_id: int, min_id: int, hash: int)` |
| `True` | `messages` | `GetMessageEditDataRequest` | `messages.GetMessageEditDataRequest` | `(self, peer: 'TypeInputPeer', id: int)` |
| `True` | `messages` | `GetMessageReactionsListRequest` | `messages.GetMessageReactionsListRequest` | `(self, peer: 'TypeInputPeer', id: int, limit: int, reaction: Optional[ForwardRef('TypeReaction')] = None, offset: Optional[str] = None)` |
| `True` | `messages` | `GetMessageReadParticipantsRequest` | `messages.GetMessageReadParticipantsRequest` | `(self, peer: 'TypeInputPeer', msg_id: int)` |
| `True` | `messages` | `GetMessagesReactionsRequest` | `messages.GetMessagesReactionsRequest` | `(self, peer: 'TypeInputPeer', id: List[int])` |
| `True` | `messages` | `GetMessagesRequest` | `messages.GetMessagesRequest` | `(self, id: List[ForwardRef('TypeInputMessage')])` |
| `True` | `messages` | `GetMessagesViewsRequest` | `messages.GetMessagesViewsRequest` | `(self, peer: 'TypeInputPeer', id: List[int], increment: bool)` |
| `True` | `messages` | `GetPeerDialogsRequest` | `messages.GetPeerDialogsRequest` | `(self, peers: List[ForwardRef('TypeInputDialogPeer')])` |
| `True` | `messages` | `GetPeerSettingsRequest` | `messages.GetPeerSettingsRequest` | `(self, peer: 'TypeInputPeer')` |
| `True` | `messages` | `GetPersonalChannelHistoryRequest` | `messages.GetPersonalChannelHistoryRequest` | `(self, user_id: 'TypeInputUser', limit: int, max_id: int, min_id: int, hash: int)` |
| `True` | `messages` | `GetPinnedDialogsRequest` | `messages.GetPinnedDialogsRequest` | `(self, folder_id: int)` |
| `True` | `messages` | `GetPinnedSavedDialogsRequest` | `messages.GetPinnedSavedDialogsRequest` | `(self, /, *args, **kwargs)` |
| `True` | `messages` | `GetPreparedInlineMessageRequest` | `messages.GetPreparedInlineMessageRequest` | `(self, bot: 'TypeInputUser', id: str)` |
| `True` | `messages` | `GetQuickReplyMessagesRequest` | `messages.GetQuickReplyMessagesRequest` | `(self, shortcut_id: int, hash: int, id: Optional[List[int]] = None)` |
| `True` | `messages` | `GetRichMessageRequest` | `messages.GetRichMessageRequest` | `(self, peer: 'TypeInputPeer', id: int)` |
| `True` | `messages` | `GetSavedDialogsByIDRequest` | `messages.GetSavedDialogsByIDRequest` | `(self, ids: List[ForwardRef('TypeInputPeer')], parent_peer: Optional[ForwardRef('TypeInputPeer')] = None)` |
| `True` | `messages` | `GetSavedDialogsRequest` | `messages.GetSavedDialogsRequest` | `(self, offset_date: Optional[datetime.datetime], offset_id: int, offset_peer: 'TypeInputPeer', limit: int, hash: int, exclude_pinned: Optional[bool] = None, parent_peer: Optional[ForwardRef('TypeInputPeer')] = None)` |
| `True` | `messages` | `GetScheduledMessagesRequest` | `messages.GetScheduledMessagesRequest` | `(self, peer: 'TypeInputPeer', id: List[int])` |
| `True` | `messages` | `GetSponsoredMessagesRequest` | `messages.GetSponsoredMessagesRequest` | `(self, peer: 'TypeInputPeer', msg_id: Optional[int] = None)` |
| `True` | `messages` | `GetSuggestedDialogFiltersRequest` | `messages.GetSuggestedDialogFiltersRequest` | `(self, /, *args, **kwargs)` |
| `True` | `messages` | `HideAllChatJoinRequestsRequest` | `messages.HideAllChatJoinRequestsRequest` | `(self, peer: 'TypeInputPeer', approved: Optional[bool] = None, link: Optional[str] = None)` |
| `True` | `messages` | `HideChatJoinRequestRequest` | `messages.HideChatJoinRequestRequest` | `(self, peer: 'TypeInputPeer', user_id: 'TypeInputUser', approved: Optional[bool] = None)` |
| `True` | `messages` | `HidePeerSettingsBarRequest` | `messages.HidePeerSettingsBarRequest` | `(self, peer: 'TypeInputPeer')` |
| `True` | `messages` | `ImportChatInviteRequest` | `messages.ImportChatInviteRequest` | `(self, hash: str)` |
| `True` | `messages` | `MarkDialogUnreadRequest` | `messages.MarkDialogUnreadRequest` | `(self, peer: 'TypeInputDialogPeer', unread: Optional[bool] = None, parent_peer: Optional[ForwardRef('TypeInputPeer')] = None)` |
| `True` | `messages` | `MigrateChatRequest` | `messages.MigrateChatRequest` | `(self, chat_id: int)` |
| `True` | `messages` | `ReadHistoryRequest` | `messages.ReadHistoryRequest` | `(self, peer: 'TypeInputPeer', max_id: int)` |
| `True` | `messages` | `ReadMessageContentsRequest` | `messages.ReadMessageContentsRequest` | `(self, id: List[int])` |
| `True` | `messages` | `ReceivedMessagesRequest` | `messages.ReceivedMessagesRequest` | `(self, max_id: int)` |
| `True` | `messages` | `ReorderPinnedDialogsRequest` | `messages.ReorderPinnedDialogsRequest` | `(self, folder_id: int, order: List[ForwardRef('TypeInputDialogPeer')], force: Optional[bool] = None)` |
| `True` | `messages` | `ReorderPinnedSavedDialogsRequest` | `messages.ReorderPinnedSavedDialogsRequest` | `(self, order: List[ForwardRef('TypeInputDialogPeer')], force: Optional[bool] = None)` |
| `True` | `messages` | `ReportMessagesDeliveryRequest` | `messages.ReportMessagesDeliveryRequest` | `(self, peer: 'TypeInputPeer', id: List[int], push: Optional[bool] = None)` |
| `True` | `messages` | `ReportSponsoredMessageRequest` | `messages.ReportSponsoredMessageRequest` | `(self, option: bytes, random_id: bytes = None)` |
| `True` | `messages` | `SavePreparedInlineMessageRequest` | `messages.SavePreparedInlineMessageRequest` | `(self, result: 'TypeInputBotInlineResult', user_id: 'TypeInputUser', peer_types: Optional[List[ForwardRef('TypeInlineQueryPeerType')]] = None)` |
| `True` | `messages` | `SendBotRequestedPeerRequest` | `messages.SendBotRequestedPeerRequest` | `(self, peer: 'TypeInputPeer', button_id: int, requested_peers: List[ForwardRef('TypeInputPeer')], msg_id: Optional[int] = None, webapp_req_id: Optional[str] = None)` |
| `True` | `messages` | `SendMessageRequest` | `messages.SendMessageRequest` | `(self, peer: 'TypeInputPeer', message: str, no_webpage: Optional[bool] = None, silent: Optional[bool] = None, background: Optional[bool] = None, clear_draft: Optional[bool] = None, noforwards: Optional[bool] = None, update_stickersets_order: Optional[bool] = None, invert_media: Optional[bool] = None, allow_paid_floodskip: Optional[bool] = None, reply_to: Optional[ForwardRef('TypeInputReplyTo')] = None, random_id: int = None, reply_markup: Optional[ForwardRef('TypeReplyMarkup')] = None, entities: Optional[List[ForwardRef('TypeMessageEntity')]] = None, schedule_date: Optional[datetime.datetime] = None, schedule_repeat_period: Optional[int] = None, send_as: Optional[ForwardRef('TypeInputPeer')] = None, quick_reply_shortcut: Optional[ForwardRef('TypeInputQuickReplyShortcut')] = None, effect: Optional[int] = None, allow_paid_stars: Optional[int] = None, suggested_post: Optional[ForwardRef('TypeSuggestedPost')] = None, rich_message: Optional[ForwardRef('TypeInputRichMessage')] = None)` |
| `True` | `messages` | `SendQuickReplyMessagesRequest` | `messages.SendQuickReplyMessagesRequest` | `(self, peer: 'TypeInputPeer', shortcut_id: int, id: List[int], random_id: List[int] = None)` |
| `True` | `messages` | `SendScheduledMessagesRequest` | `messages.SendScheduledMessagesRequest` | `(self, peer: 'TypeInputPeer', id: List[int])` |
| `True` | `messages` | `SendWebViewResultMessageRequest` | `messages.SendWebViewResultMessageRequest` | `(self, bot_query_id: str, result: 'TypeInputBotInlineResult')` |
| `True` | `messages` | `SetBotGuestChatResultRequest` | `messages.SetBotGuestChatResultRequest` | `(self, query_id: int, result: 'TypeInputBotInlineResult')` |
| `True` | `messages` | `SetChatAvailableReactionsRequest` | `messages.SetChatAvailableReactionsRequest` | `(self, peer: 'TypeInputPeer', available_reactions: 'TypeChatReactions', reactions_limit: Optional[int] = None, paid_enabled: Optional[bool] = None)` |
| `True` | `messages` | `SetChatThemeRequest` | `messages.SetChatThemeRequest` | `(self, peer: 'TypeInputPeer', theme: 'TypeInputChatTheme')` |
| `True` | `messages` | `SetChatWallPaperRequest` | `messages.SetChatWallPaperRequest` | `(self, peer: 'TypeInputPeer', for_both: Optional[bool] = None, revert: Optional[bool] = None, wallpaper: Optional[ForwardRef('TypeInputWallPaper')] = None, settings: Optional[ForwardRef('TypeWallPaperSettings')] = None, id: Optional[int] = None)` |
| `True` | `messages` | `ToggleDialogFilterTagsRequest` | `messages.ToggleDialogFilterTagsRequest` | `(self, enabled: bool)` |
| `True` | `messages` | `ToggleDialogPinRequest` | `messages.ToggleDialogPinRequest` | `(self, peer: 'TypeInputDialogPeer', pinned: Optional[bool] = None)` |
| `True` | `messages` | `TogglePeerTranslationsRequest` | `messages.TogglePeerTranslationsRequest` | `(self, peer: 'TypeInputPeer', disabled: Optional[bool] = None)` |
| `True` | `messages` | `ToggleSavedDialogPinRequest` | `messages.ToggleSavedDialogPinRequest` | `(self, peer: 'TypeInputDialogPeer', pinned: Optional[bool] = None)` |
| `True` | `messages` | `UnpinAllMessagesRequest` | `messages.UnpinAllMessagesRequest` | `(self, peer: 'TypeInputPeer', top_msg_id: Optional[int] = None, saved_peer_id: Optional[ForwardRef('TypeInputPeer')] = None)` |
| `True` | `messages` | `UpdateDialogFilterRequest` | `messages.UpdateDialogFilterRequest` | `(self, id: int, filter: Optional[ForwardRef('TypeDialogFilter')] = None)` |
| `True` | `messages` | `UpdateDialogFiltersOrderRequest` | `messages.UpdateDialogFiltersOrderRequest` | `(self, order: List[int])` |
| `True` | `messages` | `UpdatePinnedForumTopicRequest` | `messages.UpdatePinnedForumTopicRequest` | `(self, peer: 'TypeInputPeer', topic_id: int, pinned: bool)` |
| `True` | `messages` | `UpdatePinnedMessageRequest` | `messages.UpdatePinnedMessageRequest` | `(self, peer: 'TypeInputPeer', id: int, silent: Optional[bool] = None, unpin: Optional[bool] = None, pm_oneside: Optional[bool] = None)` |
| `True` | `messages` | `UpdateSavedReactionTagRequest` | `messages.UpdateSavedReactionTagRequest` | `(self, reaction: 'TypeReaction', title: Optional[str] = None)` |
| `True` | `messages` | `ViewSponsoredMessageRequest` | `messages.ViewSponsoredMessageRequest` | `(self, random_id: bytes = None)` |
| `True` | `payments` | `ToggleChatStarGiftNotificationsRequest` | `payments.ToggleChatStarGiftNotificationsRequest` | `(self, peer: 'TypeInputPeer', enabled: Optional[bool] = None)` |
| `True` | `payments` | `UpdateStarGiftCollectionRequest` | `payments.UpdateStarGiftCollectionRequest` | `(self, peer: 'TypeInputPeer', collection_id: int, title: Optional[str] = None, delete_stargift: Optional[List[ForwardRef('TypeInputSavedStarGift')]] = None, add_stargift: Optional[List[ForwardRef('TypeInputSavedStarGift')]] = None, order: Optional[List[ForwardRef('TypeInputSavedStarGift')]] = None)` |
| `True` | `payments` | `UpdateStarGiftPriceRequest` | `payments.UpdateStarGiftPriceRequest` | `(self, stargift: 'TypeInputSavedStarGift', resell_amount: 'TypeStarsAmount')` |
| `True` | `phone` | `DeleteGroupCallMessagesRequest` | `phone.DeleteGroupCallMessagesRequest` | `(self, call: 'TypeInputGroupCall', messages: List[int], report_spam: Optional[bool] = None)` |
| `True` | `phone` | `DeleteGroupCallParticipantMessagesRequest` | `phone.DeleteGroupCallParticipantMessagesRequest` | `(self, call: 'TypeInputGroupCall', participant: 'TypeInputPeer', report_spam: Optional[bool] = None)` |
| `True` | `phone` | `GetGroupCallStreamChannelsRequest` | `phone.GetGroupCallStreamChannelsRequest` | `(self, call: 'TypeInputGroupCall')` |
| `True` | `phone` | `SendGroupCallEncryptedMessageRequest` | `phone.SendGroupCallEncryptedMessageRequest` | `(self, call: 'TypeInputGroupCall', encrypted_message: bytes)` |
| `True` | `phone` | `SendGroupCallMessageRequest` | `phone.SendGroupCallMessageRequest` | `(self, call: 'TypeInputGroupCall', message: 'TypeTextWithEntities', random_id: int = None, allow_paid_stars: Optional[int] = None, send_as: Optional[ForwardRef('TypeInputPeer')] = None)` |
| `True` | `photos` | `GetUserPhotosRequest` | `photos.GetUserPhotosRequest` | `(self, user_id: 'TypeInputUser', offset: int, max_id: int, limit: int)` |
| `True` | `photos` | `UpdateProfilePhotoRequest` | `photos.UpdateProfilePhotoRequest` | `(self, id: 'TypeInputPhoto', fallback: Optional[bool] = None, bot: Optional[ForwardRef('TypeInputUser')] = None)` |
| `True` | `premium` | `GetUserBoostsRequest` | `premium.GetUserBoostsRequest` | `(self, peer: 'TypeInputPeer', user_id: 'TypeInputUser')` |
| `True` | `smsjobs` | `UpdateSettingsRequest` | `smsjobs.UpdateSettingsRequest` | `(self, allow_international: Optional[bool] = None)` |
| `True` | `stats` | `GetMessagePublicForwardsRequest` | `stats.GetMessagePublicForwardsRequest` | `(self, channel: 'TypeInputChannel', msg_id: int, offset: str, limit: int)` |
| `True` | `stats` | `GetMessageStatsRequest` | `stats.GetMessageStatsRequest` | `(self, channel: 'TypeInputChannel', msg_id: int, dark: Optional[bool] = None)` |
| `True` | `stories` | `GetAllReadPeerStoriesRequest` | `stories.GetAllReadPeerStoriesRequest` | `(self, /, *args, **kwargs)` |
| `True` | `stories` | `GetChatsToSendRequest` | `stories.GetChatsToSendRequest` | `(self, /, *args, **kwargs)` |
| `True` | `stories` | `GetPeerMaxIDsRequest` | `stories.GetPeerMaxIDsRequest` | `(self, id: List[ForwardRef('TypeInputPeer')])` |
| `True` | `stories` | `GetPeerStoriesRequest` | `stories.GetPeerStoriesRequest` | `(self, peer: 'TypeInputPeer')` |
| `True` | `stories` | `TogglePeerStoriesHiddenRequest` | `stories.TogglePeerStoriesHiddenRequest` | `(self, peer: 'TypeInputPeer', hidden: bool)` |
| `True` | `stories` | `UpdateAlbumRequest` | `stories.UpdateAlbumRequest` | `(self, peer: 'TypeInputPeer', album_id: int, title: Optional[str] = None, delete_stories: Optional[List[int]] = None, add_stories: Optional[List[int]] = None, order: Optional[List[int]] = None)` |
| `True` | `updates` | `GetChannelDifferenceRequest` | `updates.GetChannelDifferenceRequest` | `(self, channel: 'TypeInputChannel', filter: 'TypeChannelMessagesFilter', pts: int, limit: int, force: Optional[bool] = None)` |
| `True` | `updates` | `GetDifferenceRequest` | `updates.GetDifferenceRequest` | `(self, pts: int, date: Optional[datetime.datetime], qts: int, pts_limit: Optional[int] = None, pts_total_limit: Optional[int] = None, qts_limit: Optional[int] = None)` |
| `True` | `updates` | `GetStateRequest` | `updates.GetStateRequest` | `(self, /, *args, **kwargs)` |
| `True` | `users` | `GetFullUserRequest` | `users.GetFullUserRequest` | `(self, id: 'TypeInputUser')` |
| `True` | `users` | `GetRequirementsToContactRequest` | `users.GetRequirementsToContactRequest` | `(self, id: List[ForwardRef('TypeInputUser')])` |
| `True` | `users` | `GetSavedMusicByIDRequest` | `users.GetSavedMusicByIDRequest` | `(self, id: 'TypeInputUser', documents: List[ForwardRef('TypeInputDocument')])` |
| `True` | `users` | `GetSavedMusicRequest` | `users.GetSavedMusicRequest` | `(self, id: 'TypeInputUser', offset: int, limit: int, hash: int)` |
| `True` | `users` | `GetUsersRequest` | `users.GetUsersRequest` | `(self, id: List[ForwardRef('TypeInputUser')])` |
| `True` | `users` | `SetSecureValueErrorsRequest` | `users.SetSecureValueErrorsRequest` | `(self, id: 'TypeInputUser', errors: List[ForwardRef('TypeSecureValueError')])` |
| `True` | `users` | `SuggestBirthdayRequest` | `users.SuggestBirthdayRequest` | `(self, id: 'TypeInputUser', birthday: 'TypeBirthday')` |
