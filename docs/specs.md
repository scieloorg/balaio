## Modelo de dados

Tipos de entidade:

CheckIn:
* id (auto)
* articlepkg_id (foreignkey)
* checkin_id (time-based hash)
* started_at (datetime)
* finished_at (datetime)
* collection_uri (string)

ArticlePkg:
* id (auto)
* article_title (string)
* journal_pissn (string)
* journal_eissn (string)
* journal_title (string)
* issue_year (int)
* issue_volume (int)
* issue_number (int)

ValidationSet:
* id (auto)
* checkin_id (foreignkey)

Validation:
* id (auto)
* validationset_id (foreignkey)

Ticket:
* id (auto)
* articlepkg_id (foreignkey)
* description (string)
* is_solved (bool)


## Formato da mensagem

### new_checkin

Estrutura de dados a ser enviada para o endpoint *articlepkg_checkins*, 
que é responsável por receber notificações de checkins de pacotes.

```javascript
{
    "checkin_id": <string>,
    "articlepkg_id:" <string>,
    "collection_uri": <string>,
    "article_title": <string>,
    "journal_title": <string>,
    "issue_label": <string 2013 v1 n1>,
    "pkgmeta_filename": <string>,
    "pkgmeta_md5": <string>,
    "pkgmeta_filesize": <int>,
    "pkgmeta_filecount": <int>,
    "pkgmeta_submitter": <string>
}
```
