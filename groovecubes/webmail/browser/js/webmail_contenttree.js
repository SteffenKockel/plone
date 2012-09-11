// This extends the contenttree-widgets js from: 
// plone/formwidget/contenttree/jquery-contenttree/contenttree.js

if(jQuery) (function($){
    
    $.extend($.fn, {     
        contentTreeUploadFile: function() {
        	/* send the file and reload the overlay() */
        	$('input.contentTreeUploadFile').wrap(
        		'<form id="form-widgets-attachments-upload" method="post" style="display:block" />' );
        	
        	$('#form-widgets-attachments-upload').ajaxSubmit({
        		success: function(a,b,c) {
        			var response = $(a).find('#form-widgets-attachments-contenttree');
        			var newlist = $(response).html();
        			alert(newlist);
        			$('#form-widgets-attachments-contenttree').children().detach();
        			$('#form-widgets-attachments-contenttree').append(newlist);
        			$('#form-widgets-attachments-contenttree').contentTree($.fn.webmailAttachmentTreeConfig);
        			$('input.contentTreeUploadFile').unwrap()
        			} 	
        	});
        }	   
     });
     
})(jQuery);
