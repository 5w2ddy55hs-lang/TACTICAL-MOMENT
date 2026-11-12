import sys
tpl=open(sys.argv[1]).read();data=open(sys.argv[2]).read()
open(sys.argv[3],'w').write(tpl.replace('/*CLIPS*/[]',data))
