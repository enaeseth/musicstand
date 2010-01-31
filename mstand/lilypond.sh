#! /bin/sh
clear

filename=$(basename "${1##*/}" .ly)
directory=`dirname "$1"`
#echo "${directory}"$filename".pdf"
lilypondPDFoutput="${directory}"$filename".pdf"
#lilypondMIDIoutput="${directory}"/$filename".midi"

#echo $1
#echo $filename
#echo $directory
#echo $lilypondPDFoutput
#echo "done"

#key="1"

#do
echo "${directory}/${filename}"
my_home=`dirname "$0"`
"$my_home/LilyPond.app/Contents/Resources/bin/lilypond" --ps --pdf -o "${directory}/${filename}" "$1"
#wait
#open "${lilypondPDFoutput}"
#open "${lilypondMIDIoutput}"
#echo "****************************************************************"
#echo "Continue to work. When finished, save your document and choose :"
#echo "****************************************************************"
#echo "Refresh: 1"
#echo "Quit: 2"
#read key
#done
#if [ $key = "2" ]
#then exit
exit
#fi


# /Applications/LilyPond.app/Contents/Resources/bin/lilypond --ps -o "${directory}" "${fullpath}"