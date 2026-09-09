---
title: IDE Hooks
---
# IDE Hooks

## Emacs
Add the following to your ~/.emacs file
```
(defun my-c++-mode-hook ()
  (setq tab-width 4)
  (setq c-basic-offset 4)
  (define-key c++-mode-map "\C-m" 'reindent-then-newline-and-indent)
  (define-key c++-mode-map "\C-ce" 'c-comment-edit)
  (setq c++-auto-hungry-initial-state 'none)
  (setq c++-delete-function 'backward-delete-char)
  (setq c++-tab-always-indent t)
  (setq c-indent-level 4)
  (setq c-continued-statement-offset 4)
  (setq c++-empty-arglist-indent 4)
  (setq indent-tabs-mode nil))
(add-hook 'c++-mode-hook 'my-c++-mode-hook)

(add-hook 'c-mode-hook 'my-c++-mode-hook)
```